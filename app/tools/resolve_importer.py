"""
Resolve 自动导入工具
自动将素材导入到 DaVinci Resolve Media Pool
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import json


class ResolveImporter:
    """Resolve 素材导入器"""
    
    def __init__(self):
        self.resolve = None
        self.project = None
        self.media_pool = None
        self.connected = False
    
    def connect(self) -> bool:
        """
        连接到 DaVinci Resolve
        
        Returns:
            是否连接成功
        """
        try:
            from ..executor.resolve_adapter import connect_resolve
            
            self.resolve, self.project = connect_resolve()
            
            # 如果没有打开的项目，尝试创建一个
            if not self.project:
                print("没有打开的项目，尝试创建新项目...")
                project_manager = self.resolve.GetProjectManager()
                
                # 生成项目名称
                from datetime import datetime
                project_name = f"AutoCut_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # 创建新项目
                self.project = project_manager.CreateProject(project_name)
                
                if not self.project:
                    print("创建项目失败，尝试加载现有项目...")
                    # 如果创建失败，尝试加载第一个项目
                    project_manager.LoadProject(project_manager.GetProjectListInCurrentFolder()[0])
                    self.project = project_manager.GetCurrentProject()
                
                if self.project:
                    print(f"✓ 已创建/加载项目: {self.project.GetName()}")
            
            self.media_pool = self.project.GetMediaPool()
            self.connected = True
            
            return True
            
        except Exception as e:
            print(f"连接 Resolve 失败: {str(e)}")
            self.connected = False
            return False
    
    def import_media(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        导入媒体文件到 Media Pool
        
        Args:
            file_paths: 文件路径列表
        
        Returns:
            {
                "success": True/False,
                "imported": [...],  # 成功导入的文件
                "failed": [...],    # 失败的文件
                "message": "..."
            }
        """
        if not self.connected:
            if not self.connect():
                return {
                    "success": False,
                    "imported": [],
                    "failed": file_paths,
                    "message": "无法连接到 DaVinci Resolve"
                }
        
        imported = []
        failed = []
        
        try:
            # 获取当前 bin（文件夹）
            root_folder = self.media_pool.GetRootFolder()
            
            # 导入文件
            for file_path in file_paths:
                path = Path(file_path)
                
                if not path.exists():
                    failed.append({
                        "path": file_path,
                        "error": "文件不存在"
                    })
                    continue
                
                try:
                    # 使用 ImportMedia 导入
                    media_items = self.media_pool.ImportMedia([str(path)])
                    
                    if media_items:
                        imported.append({
                            "path": file_path,
                            "media_item": media_items[0] if media_items else None
                        })
                    else:
                        failed.append({
                            "path": file_path,
                            "error": "导入失败（未知原因）"
                        })
                        
                except Exception as e:
                    failed.append({
                        "path": file_path,
                        "error": str(e)
                    })
            
            success = len(imported) > 0
            message = f"成功导入 {len(imported)} 个文件"
            
            if failed:
                message += f"，{len(failed)} 个文件失败"
            
            return {
                "success": success,
                "imported": imported,
                "failed": failed,
                "message": message
            }
            
        except Exception as e:
            return {
                "success": False,
                "imported": imported,
                "failed": failed + [{"path": p, "error": str(e)} for p in file_paths if p not in [i["path"] for i in imported]],
                "message": f"导入过程出错: {str(e)}"
            }
    
    def import_from_manifest(self, manifest_path: str) -> Dict[str, Any]:
        """
        从素材清单导入
        
        Args:
            manifest_path: 素材清单文件路径 (assets_manifest.json)
        
        Returns:
            导入结果
        """
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # 提取所有素材路径
            file_paths = []
            for asset in manifest.get("assets", []):
                path = asset.get("path")
                if path:
                    file_paths.append(path)
            
            if not file_paths:
                return {
                    "success": False,
                    "imported": [],
                    "failed": [],
                    "message": "素材清单中没有文件"
                }
            
            # 导入文件
            result = self.import_media(file_paths)
            
            # 添加 asset_id 映射
            if result["success"]:
                asset_mapping = {}
                for i, asset in enumerate(manifest.get("assets", [])):
                    if i < len(result["imported"]):
                        asset_id = asset.get("asset_id")
                        media_item = result["imported"][i].get("media_item")
                        asset_mapping[asset_id] = media_item
                
                result["asset_mapping"] = asset_mapping
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "imported": [],
                "failed": [],
                "message": f"读取素材清单失败: {str(e)}"
            }
    
    def create_bin(self, bin_name: str) -> Optional[Any]:
        """
        创建 bin（文件夹）
        
        Args:
            bin_name: bin 名称
        
        Returns:
            bin 对象
        """
        if not self.connected:
            return None
        
        try:
            root_folder = self.media_pool.GetRootFolder()
            new_bin = self.media_pool.AddSubFolder(root_folder, bin_name)
            return new_bin
        except Exception as e:
            print(f"创建 bin 失败: {str(e)}")
            return None
    
    def import_to_bin(
        self,
        file_paths: List[str],
        bin_name: str
    ) -> Dict[str, Any]:
        """
        导入文件到指定 bin
        
        Args:
            file_paths: 文件路径列表
            bin_name: bin 名称
        
        Returns:
            导入结果
        """
        if not self.connected:
            if not self.connect():
                return {
                    "success": False,
                    "message": "无法连接到 DaVinci Resolve"
                }
        
        # 创建或获取 bin
        bin_folder = self.create_bin(bin_name)
        
        if not bin_folder:
            # 如果创建失败，使用 root folder
            bin_folder = self.media_pool.GetRootFolder()
        
        # 设置当前 folder
        self.media_pool.SetCurrentFolder(bin_folder)
        
        # 导入文件
        result = self.import_media(file_paths)
        
        return result
    
    def get_media_pool_items(self) -> List[Any]:
        """
        获取 Media Pool 中的所有素材
        
        Returns:
            素材列表
        """
        if not self.connected:
            return []
        
        try:
            root_folder = self.media_pool.GetRootFolder()
            clips = root_folder.GetClipList()
            return clips if clips else []
        except Exception as e:
            print(f"获取 Media Pool 素材失败: {str(e)}")
            return []
    
    def check_resolve_status(self) -> Dict[str, Any]:
        """
        检查 Resolve 状态
        
        Returns:
            {
                "connected": True/False,
                "project_name": "...",
                "media_pool_items": 10,
                "message": "..."
            }
        """
        if not self.connected:
            if not self.connect():
                return {
                    "connected": False,
                    "project_name": None,
                    "media_pool_items": 0,
                    "message": "DaVinci Resolve 未启动或未打开项目"
                }
        
        try:
            project_name = self.project.GetName()
            items = self.get_media_pool_items()
            
            return {
                "connected": True,
                "project_name": project_name,
                "media_pool_items": len(items),
                "message": f"已连接到项目: {project_name}"
            }
            
        except Exception as e:
            return {
                "connected": False,
                "project_name": None,
                "media_pool_items": 0,
                "message": f"获取项目信息失败: {str(e)}"
            }


# 单例模式
_importer_instance = None


def get_importer() -> ResolveImporter:
    """获取 ResolveImporter 单例"""
    global _importer_instance
    if _importer_instance is None:
        _importer_instance = ResolveImporter()
    return _importer_instance
