import sys
import ctypes

class WindowsTaskbar:
    def __init__(self, root):
        self.root = root
        self.ptr = None
        if sys.platform != "win32":
            return
        
        try:
            from ctypes import wintypes
            ctypes.windll.ole32.CoInitialize(0)
            
            # CLSID_TaskbarList = {56FDF344-FD6D-11d0-958A-006097C9A090}
            CLSID_TaskbarList = (ctypes.c_ubyte * 16)(0x44, 0xF3, 0xFD, 0x56, 0x6D, 0xFD, 0xD0, 0x11, 0x95, 0x8A, 0x00, 0x60, 0x97, 0xC9, 0xA0, 0x90)
            # IID_ITaskbarList3 = {ea1afb91-9e28-4b86-90e9-9e9f8a5eefaf}
            IID_ITaskbarList3 = (ctypes.c_ubyte * 16)(0x91, 0xfb, 0x1a, 0xea, 0x28, 0x9e, 0x86, 0x4b, 0x90, 0xe9, 0x9e, 0x9f, 0x8a, 0x5e, 0xef, 0xaf)
            
            self.ptr = ctypes.c_void_p()
            ret = ctypes.windll.ole32.CoCreateInstance(
                ctypes.byref(CLSID_TaskbarList), 0, 1, ctypes.byref(IID_ITaskbarList3), ctypes.byref(self.ptr)
            )
            
            if ret == 0 and self.ptr:
                # VTable 접근
                self.lpVtbl = ctypes.cast(self.ptr, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))
                # HrInit (Index 3)
                HrInit = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p)(self.lpVtbl.contents[3])
                HrInit(self.ptr)
        except Exception:
            self.ptr = None

    def set_progress(self, current, total):
        if not self.ptr or sys.platform != "win32": return
        try:
            from ctypes import wintypes
            hwnd = self.root.winfo_id()
            parent = ctypes.windll.user32.GetParent(hwnd)
            if parent: hwnd = parent
            
            # SetProgressValue (Index 9)
            SetProgressValue = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, wintypes.HWND, ctypes.c_ulonglong, ctypes.c_ulonglong)(self.lpVtbl.contents[9])
            SetProgressValue(self.ptr, hwnd, int(current), int(total))
            
            # SetProgressState (Index 10), 2 = Normal (Green)
            SetProgressState = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, wintypes.HWND, ctypes.c_int)(self.lpVtbl.contents[10])
            SetProgressState(self.ptr, hwnd, 2)
        except Exception:
            pass

    def reset(self):
        if not self.ptr or sys.platform != "win32": return
        try:
            from ctypes import wintypes
            hwnd = self.root.winfo_id()
            parent = ctypes.windll.user32.GetParent(hwnd)
            if parent: hwnd = parent
            # SetProgressState (Index 10), 0 = NoProgress
            SetProgressState = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, wintypes.HWND, ctypes.c_int)(self.lpVtbl.contents[10])
            SetProgressState(self.ptr, hwnd, 0)
        except Exception:
            pass
