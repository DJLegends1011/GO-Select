import customtkinter as ctk
import os
import sys
import shutil
import datetime
import re
import tkinter as tk
from tkinter import filedialog, messagebox
import glob
import configparser

# Set theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def parse_params_string(params_str):
    d = {}
    positional = []
    if not params_str: return d, positional
    
    parts = params_str.split(',')
    for p in parts:
        p = p.strip()
        if not p: continue
        if '=' in p:
            k, v = p.split('=', 1)
            d[k.strip().lower()] = v.strip()
        else:
            positional.append(p)
    return d, positional

def build_params_string(kv_dict, positional_list, managed_keys=[]):
    parts = []
    parts.extend(positional_list)
    for k in managed_keys:
        if k in kv_dict and kv_dict[k]:
            parts.append(f"{k}={kv_dict[k]}")
    for k, v in kv_dict.items():
        if k not in managed_keys and v:
            parts.append(f"{k}={v}")
    return ", ".join(parts)

class SlotGroupDialog(ctk.CTkToplevel):
    """Dialog for managing a slot group with multiple characters."""
    def __init__(self, parent, slot_data, available_chars, chars_dir, on_save):
        super().__init__(parent)
        self.title("Slot Group Editor")
        self.geometry("800x600")
        self.on_save = on_save
        self.available_chars = available_chars
        self.chars_dir = chars_dir
        
        self.characters = []
        if slot_data:
            if slot_data.get("type") == "slot":
                self.characters = [c.copy() for c in slot_data.get("characters", [])]
            elif slot_data.get("type") == "single" and slot_data.get("char"):
                self.characters = [{"char": slot_data["char"], "next": "w", "previous": "s", "select": ""}]
        
        self.create_widgets()
        self.transient(parent)
        self.lift()
        self.focus_force()
        self.grab_set()

    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(header, text="Slot Group Editor", font=("Arial", 18, "bold")).pack(side="left")
        ctk.CTkLabel(header, text="Characters share same grid position. First = primary.", text_color="gray").pack(side="left", padx=20)
        
        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=10, pady=5)
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=2)
        main.grid_rowconfigure(0, weight=1)
        
        left_frame = ctk.CTkFrame(main)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(left_frame, text="Available Characters", font=("Arial", 12, "bold")).pack(pady=5)
        self.char_search = ctk.CTkEntry(left_frame, placeholder_text="Search...")
        self.char_search.pack(fill="x", padx=5, pady=5)
        self.char_search.bind("<KeyRelease>", self.filter_chars)
        self.char_listbox = ctk.CTkScrollableFrame(left_frame)
        self.char_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.populate_char_list()
        
        right_frame = ctk.CTkFrame(main)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(right_frame, text="Characters in Slot (First = Primary)", font=("Arial", 12, "bold")).pack(pady=5)
        self.slot_list_frame = ctk.CTkScrollableFrame(right_frame)
        self.slot_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.refresh_slot_list()
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy, fg_color="gray").pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Save Slot Group", command=self.save, fg_color="green").pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Convert to Single", command=self.convert_to_single).pack(side="left", padx=5)

    def populate_char_list(self, filter_text=""):
        for w in self.char_listbox.winfo_children(): w.destroy()
        filter_text = filter_text.lower()
        for char in self.available_chars:
            if filter_text and filter_text not in char.lower(): continue
            ctk.CTkButton(self.char_listbox, text=char, anchor="w", command=lambda c=char: self.add_char_to_slot(c)).pack(fill="x", pady=1)

    def filter_chars(self, event=None):
        self.populate_char_list(self.char_search.get())

    def add_char_to_slot(self, char_name):
        self.characters.append({"char": char_name, "next": "w", "previous": "s", "select": ""})
        self.refresh_slot_list()

    def refresh_slot_list(self):
        for w in self.slot_list_frame.winfo_children(): w.destroy()
        for i, char_data in enumerate(self.characters):
            frame = ctk.CTkFrame(self.slot_list_frame)
            frame.pack(fill="x", pady=2)
            frame.grid_columnconfigure(1, weight=1)
            
            pos_text = "★ " if i == 0 else f"{i+1}. "
            pos_color = "#FFD700" if i == 0 else "white"
            ctk.CTkLabel(frame, text=pos_text, text_color=pos_color, width=30).grid(row=0, column=0, rowspan=2)
            ctk.CTkLabel(frame, text=char_data["char"], font=("Arial", 11, "bold"), anchor="w").grid(row=0, column=1, sticky="w", padx=5)
            
            params_frame = ctk.CTkFrame(frame, fg_color="transparent")
            params_frame.grid(row=1, column=1, sticky="w", padx=5)
            
            ctk.CTkLabel(params_frame, text="Next:", text_color="gray").pack(side="left")
            next_entry = ctk.CTkEntry(params_frame, width=50)
            next_entry.insert(0, char_data.get("next", "w"))
            next_entry.pack(side="left", padx=2)
            next_entry.bind("<KeyRelease>", lambda e, idx=i, ent=next_entry: self.update_char_param(idx, "next", ent.get()))
            
            ctk.CTkLabel(params_frame, text="Prev:", text_color="gray").pack(side="left", padx=(10,0))
            prev_entry = ctk.CTkEntry(params_frame, width=50)
            prev_entry.insert(0, char_data.get("previous", "s"))
            prev_entry.pack(side="left", padx=2)
            prev_entry.bind("<KeyRelease>", lambda e, idx=i, ent=prev_entry: self.update_char_param(idx, "previous", ent.get()))
            
            ctk.CTkLabel(params_frame, text="Select:", text_color="gray").pack(side="left", padx=(10,0))
            select_entry = ctk.CTkEntry(params_frame, width=60)
            select_entry.insert(0, char_data.get("select", ""))
            select_entry.pack(side="left", padx=2)
            select_entry.bind("<KeyRelease>", lambda e, idx=i, ent=select_entry: self.update_char_param(idx, "select", ent.get()))
            
            btn_frame2 = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame2.grid(row=0, column=2, rowspan=2, padx=5)
            if i > 0:
                ctk.CTkButton(btn_frame2, text="↑", width=25, command=lambda idx=i: self.move_char(idx, -1)).pack(side="left", padx=1)
            if i < len(self.characters) - 1:
                ctk.CTkButton(btn_frame2, text="↓", width=25, command=lambda idx=i: self.move_char(idx, 1)).pack(side="left", padx=1)
            ctk.CTkButton(btn_frame2, text="✕", width=25, fg_color="red", command=lambda idx=i: self.remove_char(idx)).pack(side="left", padx=1)

    def update_char_param(self, index, key, value):
        if 0 <= index < len(self.characters): self.characters[index][key] = value

    def move_char(self, index, direction):
        new_index = index + direction
        if 0 <= new_index < len(self.characters):
            self.characters[index], self.characters[new_index] = self.characters[new_index], self.characters[index]
            self.refresh_slot_list()

    def remove_char(self, index):
        if 0 <= index < len(self.characters):
            del self.characters[index]
            self.refresh_slot_list()

    def convert_to_single(self):
        if self.characters:
            self.on_save({"type": "single", "char": self.characters[0]["char"], "params": ""})
        self.destroy()

    def save(self):
        if not self.characters:
            messagebox.showerror("Error", "Slot group must have at least one character")
            return
        self.on_save({"type": "slot", "characters": self.characters})
        self.destroy()


class StagePropertiesDialog(ctk.CTkToplevel):
    def __init__(self, parent, stage_line, on_save):
        super().__init__(parent)
        self.title("Stage Properties")
        self.geometry("500x600")
        self.on_save = on_save
        
        self.params_dict, self.positional = parse_params_string(stage_line)
        self.stage_path = self.positional[0] if self.positional else ""
        
        self.create_widgets()
        self.transient(parent)
        self.lift()
        self.focus_force()
        self.grab_set()

    def create_widgets(self):
        self.main_frame = ctk.CTkScrollableFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.entries = {}
        
        # Main Stage Path
        lbl = ctk.CTkLabel(self.main_frame, text="Stage Path")
        lbl.pack(pady=(5,0))
        entry_path = ctk.CTkEntry(self.main_frame, width=300)
        entry_path.insert(0, self.stage_path)
        entry_path.pack(pady=5)
        self.entries["path"] = entry_path
        
        # Params
        fields = [
            ("music", "Music", "sound/music.mp3"),
            ("final.music", "Final Round Music", "sound/final.mp3"),
            ("victory.music", "Victory Music", "sound/win.mp3"),
            ("round.music", "Round Music (Generic)", ""),
            ("life.music", "Low Life Music", ""),
            ("order", "Order", "1"),
            ("unlock", "Unlock (Lua)", "return true")
        ]
        
        for i in range(1, 4):
            fields.insert(1+i, (f"round{i}.music", f"Round {i} Music", ""))

        for key, label, example in fields:
            lbl = ctk.CTkLabel(self.main_frame, text=label)
            lbl.pack(pady=(5,0))
            entry = ctk.CTkEntry(self.main_frame, width=300, placeholder_text=example)
            entry.pack(pady=2)
            if key in self.params_dict:
                entry.insert(0, self.params_dict[key])
            self.entries[key] = entry
            
        btn = ctk.CTkButton(self, text="Save", command=self.save)
        btn.pack(pady=10)

    def save(self):
        new_path = self.entries["path"].get().strip()
        if not new_path:
            messagebox.showerror("Error", "Stage path cannot be empty")
            return
            
        new_positional = [new_path]
        new_dict = self.params_dict.copy()
        
        keys = ["music", "final.music", "victory.music", "life.music", "order", "unlock"]
        for i in range(1,4): keys.append(f"round{i}.music")
        
        for k in keys:
            if k in self.entries:
                val = self.entries[k].get().strip()
                if val: new_dict[k] = val
                elif k in new_dict: del new_dict[k]
                
        result = build_params_string(new_dict, new_positional, keys)
        self.on_save(result)
        self.destroy()

class CharPropertiesDialog(ctk.CTkToplevel):
    def __init__(self, parent, char_name, full_path, current_params, on_save):
        super().__init__(parent)
        self.title(f"Properties: {char_name}")
        self.geometry("650x700")
        self.full_path = full_path
        self.on_save = on_save
        
        self.params_dict, self.stages_list = parse_params_string(current_params)
        self.char_info = self.parse_char_def()
        
        self.create_widgets()
        self.transient(parent)
        self.lift()
        self.focus_force()
        self.grab_set()

    def parse_char_def(self):
        info = {}
        if not self.full_path or not os.path.exists(self.full_path):
            info["Status"] = "Definition file not found"
            return info
        if os.path.isdir(self.full_path):
             info["Status"] = "Error: Path is a directory"
             return info
        try:
            with open(self.full_path, 'r', encoding='utf-8', errors='ignore') as f:
                in_info = False
                for line in f:
                    line = line.strip()
                    if line.lower().startswith('[info]'):
                        in_info = True
                        continue
                    if line.startswith('[') and in_info: break
                    if in_info and '=' in line:
                        k, v = line.split('=', 1)
                        info[k.strip().lower()] = v.strip().strip('"')
        except Exception as e:
            info["Error"] = str(e)
        return info

    def create_widgets(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_config = self.tabview.add("Configure")
        self.tab_details = self.tabview.add("Details")
        self.tab_music = self.tabview.add("Music")
        
        # Details
        details_frame = ctk.CTkScrollableFrame(self.tab_details)
        details_frame.pack(fill="both", expand=True)
        r=0
        for k,v in self.char_info.items():
            ctk.CTkLabel(details_frame, text=k.capitalize(), font=("Arial",12,"bold")).grid(row=r,column=0,sticky="w",padx=10)
            ctk.CTkLabel(details_frame, text=v).grid(row=r,column=1,sticky="w",padx=10)
            r+=1
            
        # Configure
        config_frame = ctk.CTkScrollableFrame(self.tab_config)
        config_frame.pack(fill="both", expand=True)
        self.entries = {}
        
        r=0
        
        # Standard Params
        ctk.CTkLabel(config_frame, text="--- Standard Params ---", text_color="gray").grid(row=r,column=0,columnspan=2,pady=(5,5))
        r+=1
        
        fields_std = [
            ("stage", "Stage Path", "stages/kfm.def"),
            ("music", "Music Path", "sound/bgm.mp3"),
            ("order", "Order", "1"),
            ("ai", "AI Level", "1-8"),
            ("vsscreen", "VS Screen (0/1)", "1"),
            ("victoryscreen", "Victory Screen (0/1)", "1"),
            ("rounds", "Rounds", "2"),
            ("time", "Time (Seconds)", "-1"),
            ("includestage", "Include Stage (0/1/-1)", "1")
        ]
        
        for key, label, example in fields_std:
            ctk.CTkLabel(config_frame, text=label).grid(row=r, column=0, sticky="w", padx=10, pady=2)
            if key == "stage":
                entry = ctk.CTkEntry(config_frame, width=250, placeholder_text=example)
                if self.stages_list: entry.insert(0, ", ".join(self.stages_list))
                entry.grid(row=r, column=1, sticky="w", padx=10)
                self.entries[key] = entry
            else:
                entry = ctk.CTkEntry(config_frame, width=250, placeholder_text=example)
                if key in self.params_dict: entry.insert(0, self.params_dict[key])
                entry.grid(row=r, column=1, sticky="w", padx=10)
                self.entries[key] = entry
            r+=1

        # Ikemen Params
        ctk.CTkLabel(config_frame, text="--- Ikemen Params ---", text_color="gray").grid(row=r,column=0,columnspan=2,pady=(10,5))
        r+=1
        
        fields_ikemen = [
            ("single", "Single Mode (0/1)", "0"),
            ("bonus", "Bonus Game (0/1)", "0"),
            ("exclude", "Exclude (0/1)", "0"),
            ("hidden", "Hidden (0/1/2/3)", "0"),
            ("ordersurvival", "Survival Order", "1"),
            ("arcadepath", "Arcade Path (Lua)", "data/arcade.lua"),
            ("ratiopath", "Ratio Path (Lua)", "data/ratio.lua"),
            ("unlock", "Unlock (Lua)", "true"),
        ]
        
        for key, label, example in fields_ikemen:
            ctk.CTkLabel(config_frame, text=label).grid(row=r, column=0, sticky="w", padx=10, pady=2)
            
            if key == "exclude":
                var = ctk.BooleanVar(value=False)
                if key in self.params_dict and self.params_dict[key] == "1": var.set(True)
                entry = ctk.CTkCheckBox(config_frame, text="Exclude", variable=var)
                entry.grid(row=r, column=1, sticky="w", padx=10)
                self.entries[key] = entry
            else:
                entry = ctk.CTkEntry(config_frame, width=250, placeholder_text=example)
                if key in self.params_dict: entry.insert(0, self.params_dict[key])
                entry.grid(row=r, column=1, sticky="w", padx=10)
                self.entries[key] = entry
            r+=1

        # Slot Params
        ctk.CTkLabel(config_frame, text="--- Slot Params (Inside 'slot={}') ---", text_color="gray").grid(row=r,column=0,columnspan=2,pady=(10,5))
        r+=1
        fields_slot = [
            ("select", "Select Command", "/s+a"),
            ("next", "Next Command", "w"),
            ("previous", "Previous Command", "d")
        ]
        for key, label, example in fields_slot:
            ctk.CTkLabel(config_frame, text=label).grid(row=r, column=0, sticky="w", padx=10, pady=2)
            entry = ctk.CTkEntry(config_frame, width=250, placeholder_text=example)
            if key in self.params_dict: entry.insert(0, self.params_dict[key])
            entry.grid(row=r, column=1, sticky="w", padx=10)
            self.entries[key] = entry
            r+=1

        # Music Tab
        music_frame = ctk.CTkScrollableFrame(self.tab_music)
        music_frame.pack(fill="both", expand=True)
        r=0
        music_fields = [
            ("final.music", "Final Round Music"),
            ("victory.music", "Victory Music"),
            ("life.music", "Low Life Music"),
            ("round.music", "Round Music (Generic)")
        ]
        for i in range(1, 10):
            music_fields.insert(i-1, (f"round{i}.music", f"Round {i} Music"))
        
        for key, label in music_fields:
            ctk.CTkLabel(music_frame, text=label).grid(row=r,column=0,sticky="w",padx=10,pady=5)
            entry = ctk.CTkEntry(music_frame, width=300)
            if key in self.params_dict: entry.insert(0, self.params_dict[key])
            entry.grid(row=r,column=1,sticky="w",padx=10)
            self.entries[key] = entry
            r+=1

        ctk.CTkButton(self, text="OK", command=self.save).pack(pady=10)

    def save(self):
        new_dict = self.params_dict.copy()
        
        managed = ["music", "order", "ai", "rounds", "time", "vsscreen", "victoryscreen", "exclude", 
                   "single", "bonus", "includestage",
                   "hidden", "unlock", "arcadepath", "ratiopath", "ordersurvival",
                   "select", "next", "previous",
                   "final.music", "victory.music", "life.music", "round.music"]
        for i in range(1,10): managed.append(f"round{i}.music")
        
        if self.entries["exclude"].get():
            new_dict["exclude"] = "1"
        elif "exclude" in new_dict:
            del new_dict["exclude"]
            
        for k in managed:
            if k == "exclude": continue
            if k in self.entries:
                val = self.entries[k].get().strip()
                if val: new_dict[k] = val
                elif k in new_dict: del new_dict[k]
            
        new_stages = []
        stage_val = self.entries["stage"].get().strip()
        if stage_val: new_stages.append(stage_val)
        
        result = build_params_string(new_dict, new_stages, managed)
        self.on_save(result)
        self.destroy()

class OptionsDialog(ctk.CTkToplevel):
    def __init__(self, parent, current_config, on_save):
        super().__init__(parent)
        self.title("Options")
        self.geometry("400x300")
        self.config = current_config
        self.on_save = on_save
        self.create_widgets()
        self.transient(parent)
        self.lift()
        self.focus_force()
        self.grab_set()
        
    def create_widgets(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_adv = self.tabview.add("Advanced")
        
        # Options File
        adv_frame = ctk.CTkFrame(self.tab_adv, fg_color="transparent")
        adv_frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(adv_frame, text="Options file", font=("Arial", 12, "bold")).pack(anchor="w")
        
        val_local = self.config.getboolean("Options", "UseLocal", fallback=True)
        self.var_local = ctk.BooleanVar(value=val_local)
        ctk.CTkCheckBox(adv_frame, text="Use local options file", variable=self.var_local).pack(anchor="w", padx=10, pady=5)
        
        # Backups
        ctk.CTkLabel(adv_frame, text="Backups", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10,0))
        val_bk = self.config.getboolean("Options", "Backup", fallback=True)
        self.var_backup = ctk.BooleanVar(value=val_bk)
        ctk.CTkCheckBox(adv_frame, text="Make a backup before every save", variable=self.var_backup).pack(anchor="w", padx=10, pady=5)

        ctk.CTkButton(self, text="OK", command=self.save).pack(pady=10)
        
    def save(self):
        if "Options" not in self.config: self.config["Options"] = {}
        self.config["Options"]["UseLocal"] = str(self.var_local.get())
        self.config["Options"]["Backup"] = str(self.var_backup.get())
        self.on_save(self.config)
        self.destroy()

class GOSelect(ctk.CTk):
    def __init__(self, base_path=None):
        super().__init__()
        self.title("GO-Select")
        self.geometry("1400x800") 
        
        self.base_path = None

        # Config Init
        self.config = configparser.ConfigParser()
        self.local_cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "go_select.ini")
        self.global_dir = os.path.join(os.getenv('APPDATA'), "GO-Select") if os.getenv('APPDATA') else os.path.expanduser("~/.config/GO-Select")
        self.global_cfg = os.path.join(self.global_dir, "go_select.ini")
        
        self.load_config()
        if base_path: self.base_path = base_path
        if not self.base_path: self.base_path = os.getcwd()

        self.rows = 10
        self.cols = 10
        self.available_chars = []
        self.available_stages = [] 
        self.slots = []
        self.extra_stages = [] 
        self.sections = {"pre":[], "chars":[], "mid":[], "stages":[], "post":[]}
        self.selected_slot_index = None

        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=3) 
        self.grid_columnconfigure(2, weight=1) 
        self.grid_rowconfigure(0, weight=1)

        self.update_paths()
        self.create_widgets()
        
        if not os.path.exists(self.select_def_path):
             self.ask_system_def()
        else:
            self.find_grid_dimensions()
            self.load_data()

    def update_paths(self):
        self.chars_dir = os.path.join(self.base_path, "chars")
        self.stages_dir = os.path.join(self.base_path, "stages")
        self.data_dir = os.path.join(self.base_path, "data")
        self.select_def_path = os.path.join(self.data_dir, "select.def")

    def load_config(self):
        if os.path.exists(self.local_cfg):
            self.config.read(self.local_cfg)
        elif os.path.exists(self.global_cfg):
            self.config.read(self.global_cfg)
            
        if "Paths" in self.config and "MugenRoot" in self.config["Paths"]:
            val = self.config["Paths"]["MugenRoot"]
            if val and os.path.exists(val):
                self.base_path = val
        
        # Also restore select_def_path if saved
        if "Paths" in self.config and "SelectDef" in self.config["Paths"]:
            val = self.config["Paths"]["SelectDef"]
            if val and os.path.exists(val):
                self.select_def_path = val
                self.data_dir = os.path.dirname(val)

    def save_config(self):
        use_local = self.config.getboolean("Options", "UseLocal", fallback=True)
        target = self.local_cfg if use_local else self.global_cfg
        
        if not use_local:
            if not os.path.exists(self.global_dir): os.makedirs(self.global_dir)
            if os.path.exists(self.local_cfg): 
                try: os.remove(self.local_cfg)
                except: pass
        
        if "Paths" not in self.config: self.config["Paths"] = {}
        if self.base_path: self.config["Paths"]["MugenRoot"] = self.base_path
        if hasattr(self, 'select_def_path') and self.select_def_path:
            self.config["Paths"]["SelectDef"] = self.select_def_path
        
        try:
            with open(target, 'w') as f: self.config.write(f)
        except Exception as e: messagebox.showerror("Config Error", str(e))

    def find_select_def_from_system(self, system_def_path):
        """Parse system.def to find the actual select.def path."""
        system_dir = os.path.dirname(system_def_path)
        select_path = None
        
        try:
            with open(system_def_path, 'r', encoding='utf-8', errors='ignore') as f:
                in_files = False
                for line in f:
                    stripped = line.strip()
                    # Check for [Files] section
                    if stripped.lower().startswith('[files]'):
                        in_files = True
                        continue
                    if stripped.startswith('[') and in_files:
                        break
                    if in_files and '=' in stripped:
                        # Remove comments
                        if ';' in stripped:
                            stripped = stripped.split(';')[0].strip()
                        key, value = stripped.split('=', 1)
                        key = key.strip().lower()
                        value = value.strip().strip('"')
                        if key == 'select':
                            # Path is relative to game root, not system.def location
                            select_path = value
                            break
        except Exception as e:
            print(f"Error parsing system.def: {e}")
        
        return select_path

    def ask_system_def(self):
        msg = "Please locate the 'system.def' file for your Mugen/Ikemen game.\nThis is usually in the 'data' folder."
        messagebox.showinfo("Setup", msg)
        path = filedialog.askopenfilename(title="Select system.def", filetypes=[("Definition", "*.def"), ("All Files", "*.*")])
        if path:
            data_dir = os.path.dirname(path)
            base = os.path.dirname(data_dir)
            self.base_path = base
            
            # Try to find select.def path from system.def
            select_rel_path = self.find_select_def_from_system(path)
            
            if select_rel_path:
                # Path in system.def is relative to game root
                self.select_def_path = os.path.join(self.base_path, select_rel_path)
                # Update data_dir to be wherever select.def is
                self.data_dir = os.path.dirname(self.select_def_path)
            else:
                # Fallback to default location
                self.update_paths()
            
            self.save_config()
            
            if os.path.exists(self.select_def_path):
                self.find_grid_dimensions()
                self.load_data()
            else:
                # Ask user to locate select.def manually
                messagebox.showwarning("Warning", f"Could not find select.def at:\n{self.select_def_path}\n\nPlease locate it manually.")
                select_path = filedialog.askopenfilename(title="Select select.def", filetypes=[("Definition", "*.def"), ("All Files", "*.*")])
                if select_path and os.path.exists(select_path):
                    self.select_def_path = select_path
                    self.data_dir = os.path.dirname(select_path)
                    self.save_config()
                    self.find_grid_dimensions()
                    self.load_data()
                else:
                    messagebox.showerror("Error", "Could not find select.def. Exiting.")
                    self.destroy()
                    sys.exit()
        else:
             if not self.base_path or not os.path.exists(self.select_def_path):
                 messagebox.showerror("Error", "Setup cancelled or invalid. Exiting.")
                 self.destroy()
                 sys.exit()

    def find_grid_dimensions(self):
        cfg_path = os.path.join(self.data_dir, "mugen.cfg")
        motif_path = os.path.join(self.data_dir, "system.def")
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path,'r',encoding='utf-8',errors='ignore') as f:
                    for l in f:
                        if l.strip().lower().startswith("motif"):
                            p = l.split("=",1)[1].strip()
                            if os.path.exists(os.path.join(self.base_path,p)): motif_path = os.path.join(self.base_path,p)
            except: pass
        if os.path.exists(motif_path):
            try:
                with open(motif_path,'r',encoding='utf-8',errors='ignore') as f:
                    reading=False
                    for l in f:
                        l=l.strip()
                        if l.lower().startswith("[select info]"): reading=True; continue
                        if l.startswith("[") and reading: break
                        if reading:
                            if l.lower().startswith("rows"): self.rows = int(l.split("=")[1].split(",")[0].strip())
                            if l.lower().startswith("columns"): self.cols = int(l.split("=")[1].split(",")[0].strip())
            except: pass

    def create_widgets(self):
        # --- Left: Chars ---
        self.sidebar = ctk.CTkFrame(self, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(self.sidebar, text="Characters", font=("Arial",16,"bold")).grid(row=0,column=0,pady=10)
        ctk.CTkButton(self.sidebar, text="Rescan", command=self.scan_content).grid(row=1,column=0,pady=5)
        self.char_list_frame = ctk.CTkScrollableFrame(self.sidebar, label_text="Available")
        self.char_list_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        # --- Center: Grid ---
        self.main_area = ctk.CTkFrame(self, corner_radius=0)
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_rowconfigure(1, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)
        
        self.toolbar = ctk.CTkFrame(self.main_area, height=40)
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        ctk.CTkButton(self.toolbar, text="Options", command=self.open_options, width=80).pack(side="right", padx=5)
        ctk.CTkButton(self.toolbar, text="Save select.def", command=self.save_select_def, fg_color="green").pack(side="right", padx=5)
        self.param_entry = ctk.CTkEntry(self.toolbar, placeholder_text="Quick Params", width=250)
        self.param_entry.pack(side="left", padx=5)
        ctk.CTkButton(self.toolbar, text="Update", command=self.update_current_slot_params, width=60).pack(side="left")

        self.grid_container = ctk.CTkFrame(self.main_area, corner_radius=0, fg_color="transparent")
        self.grid_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.grid_container.grid_rowconfigure(0, weight=1)
        self.grid_container.grid_columnconfigure(0, weight=1)
        
        self.grid_canvas = tk.Canvas(self.grid_container, highlightthickness=0, bg="#2B2B2B")
        self.grid_canvas.grid(row=0, column=0, sticky="nsew")
        
        self.v_scroll = ctk.CTkScrollbar(self.grid_container, orientation="vertical", command=self.grid_canvas.yview)
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.h_scroll = ctk.CTkScrollbar(self.grid_container, orientation="horizontal", command=self.grid_canvas.xview)
        self.h_scroll.grid(row=1, column=0, sticky="ew")
        
        self.grid_canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        
        self.grid_frame = ctk.CTkFrame(self.grid_canvas, fg_color="#2B2B2B")
        self.grid_window_id = self.grid_canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        
        def _update_layout(e):
            self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all"))
            # Center logic
            cw = self.grid_canvas.winfo_width()
            ch = self.grid_canvas.winfo_height()
            fw = self.grid_frame.winfo_reqwidth()
            fh = self.grid_frame.winfo_reqheight()
            x, y = 0, 0
            if fw < cw: x = (cw - fw) // 2
            if fh < ch: y = (ch - fh) // 2
            self.grid_canvas.coords(self.grid_window_id, x, y)
            
        self.grid_frame.bind("<Configure>", _update_layout)
        self.grid_canvas.bind("<Configure>", _update_layout)

        self.status_bar = ctk.CTkLabel(self.main_area, text="Ready", anchor="w")
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=5)

        # --- Right: Stages ---
        self.stage_sidebar = ctk.CTkFrame(self, corner_radius=0)
        self.stage_sidebar.grid(row=0, column=2, sticky="nsew")
        self.stage_sidebar.grid_rowconfigure(2, weight=1)
        self.stage_sidebar.grid_rowconfigure(4, weight=1)
        
        ctk.CTkLabel(self.stage_sidebar, text="Extra Stages", font=("Arial",16,"bold")).grid(row=0,column=0,pady=10)
        
        # Add a Rescan button to align with Chars column
        ctk.CTkButton(self.stage_sidebar, text="Rescan", command=self.scan_content).grid(row=1,column=0,pady=5)
        
        self.scanned_stage_frame = ctk.CTkScrollableFrame(self.stage_sidebar, label_text="Available Stages", height=200)
        self.scanned_stage_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        
        controls = ctk.CTkFrame(self.stage_sidebar)
        controls.grid(row=3, column=0, pady=5)
        ctk.CTkButton(controls, text="Add Selected", command=self.add_stage, width=100).pack(pady=2)
        
        self.extra_stage_frame = ctk.CTkScrollableFrame(self.stage_sidebar, label_text="Selected Stages")
        self.extra_stage_frame.grid(row=4, column=0, sticky="nsew", padx=5, pady=5)

    def scan_content(self):
        self.scan_characters()
        self.scan_stages()

    def scan_characters(self):
        for w in self.char_list_frame.winfo_children(): w.destroy()
        if not os.path.exists(self.chars_dir): return
        
        self.available_chars = []
        for root, dirs, files in os.walk(self.chars_dir):
            for file in files:
                if file.lower().endswith(".def"):
                    full = os.path.join(root, file)
                    rel = os.path.relpath(full, self.chars_dir).replace("\\", "/")
                    folder = os.path.basename(os.path.dirname(full))
                    fname = os.path.splitext(file)[0]
                    if folder.lower() == fname.lower() and rel.count('/')==1: rel = folder
                    self.available_chars.append(rel)
        self.available_chars.sort()
        for c in self.available_chars:
            ctk.CTkButton(self.char_list_frame, text=c, anchor="w", command=lambda x=c: self.assign_char_to_slot(x)).pack(fill="x", pady=1)

    def scan_stages(self):
        for w in self.scanned_stage_frame.winfo_children(): w.destroy()
        if not os.path.exists(self.stages_dir): return
        
        self.available_stages = []
        for root, dirs, files in os.walk(self.stages_dir):
            for file in files:
                if file.lower().endswith(".def"):
                    full = os.path.join(root, file)
                    rel = os.path.relpath(full, self.stages_dir).replace("\\", "/")
                    path_str = f"stages/{rel}"
                    # Display name only
                    display = os.path.splitext(os.path.basename(file))[0]
                    self.available_stages.append((path_str, display))
        
        self.available_stages.sort(key=lambda x: x[1])
        for path, display in self.available_stages:
            ctk.CTkButton(self.scanned_stage_frame, text=display, anchor="w", command=lambda x=path: self.preview_stage_add(x)).pack(fill="x", pady=1)

    def preview_stage_add(self, stage_path):
        self.extra_stages.append(stage_path)
        self.refresh_extra_stages()

    def add_stage(self):
        pass

    def load_data(self):
        self.slots = []  # Each slot is {"type": "single", "char": "", "params": ""} or {"type": "slot", "characters": [...]}
        self.extra_stages = []
        self.sections = {"pre":[], "chars":[], "mid":[], "stages":[], "post":[]}
        current_section = "pre"
        in_slot_block = False
        slot_block_chars = []
        
        try:
            with open(self.select_def_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    clean = line.strip().lower()
                    if clean.startswith("[characters]"):
                        self.sections["pre"].append(line)
                        current_section = "chars"
                        continue
                    elif clean.startswith("[extrastages]"):
                        current_section = "stages"
                        self.sections["mid"].append(line)
                        continue
                    elif clean.startswith("["):
                        current_section = "post"
                        self.sections["post"].append(line)
                        continue
                        
                    if current_section == "pre": self.sections["pre"].append(line)
                    elif current_section == "chars":
                        content = line.split(';', 1)[0].strip()
                        if not content: continue
                        
                        # Check for slot block start
                        if content.lower().startswith("slot") and "=" in content and "{" in content:
                            in_slot_block = True
                            slot_block_chars = []
                            # Check if there's content after { on the same line
                            after_brace = content.split("{", 1)[1].strip() if "{" in content else ""
                            if after_brace and after_brace != "}":
                                self._parse_slot_char(after_brace, slot_block_chars)
                            continue
                        
                        # Inside slot block
                        if in_slot_block:
                            if "}" in content:
                                # End of slot block
                                before_brace = content.split("}")[0].strip()
                                if before_brace:
                                    self._parse_slot_char(before_brace, slot_block_chars)
                                if slot_block_chars:
                                    self.slots.append({"type": "slot", "characters": slot_block_chars})
                                in_slot_block = False
                                slot_block_chars = []
                            else:
                                self._parse_slot_char(content, slot_block_chars)
                            continue
                        
                        # Regular single character
                        parts = content.split(',', 1)
                        char = parts[0].strip()
                        params = parts[1].strip() if len(parts)>1 else ""
                        self.slots.append({"type": "single", "char": char, "params": params})
                        
                    elif current_section == "stages":
                        content = line.split(';', 1)[0].strip()
                        if content: self.extra_stages.append(content)
                    elif current_section == "post": self.sections["post"].append(line)
            self.scan_content()
            self.refresh_grid()
            self.refresh_extra_stages()
        except Exception as e: messagebox.showerror("Error", f"Load failed: {e}")
    
    def _parse_slot_char(self, content, slot_block_chars):
        """Parse a character line inside a slot block."""
        params_dict, positional = parse_params_string(content)
        char_name = positional[0] if positional else ""
        if char_name:
            slot_block_chars.append({
                "char": char_name,
                "next": params_dict.get("next", "w"),
                "previous": params_dict.get("previous", "s"),
                "select": params_dict.get("select", "")
            })

    def refresh_grid(self):
        for w in self.grid_frame.winfo_children(): w.destroy()
        for i in range(self.rows * self.cols):
            r, c = i // self.cols, i % self.cols
            
            if i < len(self.slots):
                slot = self.slots[i]
                if slot.get("type") == "slot":
                    # Slot group - show primary character with indicator
                    chars = slot.get("characters", [])
                    char = chars[0]["char"] if chars else "Empty"
                    char_count = len(chars)
                    display_text = f"{char[:6]}[{char_count}]" if char else f"Slot[{char_count}]"
                    fg = "#664422"  # Orange-ish for slot groups
                    border_color = "#FFD700"  # Gold border
                else:
                    # Single character
                    char = slot.get("char", "")
                    if not char: char = "Empty"
                    display_text = char[:8]
                    fg = "transparent"
                    if char.lower() == "randomselect": fg = "#442244"
                    elif char != "Empty": fg = "#224422"
                    border_color = "gray"
            else:
                display_text = "Empty"
                fg = "transparent"
                border_color = "gray"
            
            btn = ctk.CTkButton(self.grid_frame, text=display_text, width=60, height=30, fg_color=fg, border_width=2, border_color=border_color, command=lambda idx=i: self.select_slot(idx))
            btn.grid(row=r, column=c, padx=1, pady=1)
            btn.bind("<Button-3>", lambda e, idx=i: self.show_context_menu(e, idx))

    def refresh_extra_stages(self):
        for w in self.extra_stage_frame.winfo_children(): w.destroy()
        
        for i, stage_line in enumerate(self.extra_stages):
            path = stage_line.split(',', 1)[0].strip()
            
            # Using grid instead of pack to handle resize/overflow better
            f = ctk.CTkFrame(self.extra_stage_frame)
            f.pack(fill="x", pady=1)
            f.grid_columnconfigure(0, weight=1)
            
            lbl = ctk.CTkLabel(f, text=path, anchor="w")
            lbl.grid(row=0, column=0, sticky="ew", padx=5)
            
            btn_frame = ctk.CTkFrame(f, fg_color="transparent")
            btn_frame.grid(row=0, column=1, sticky="e")
            
            ctk.CTkButton(btn_frame, text="⚙", width=30, command=lambda idx=i: self.edit_stage(idx)).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="X", width=30, fg_color="red", command=lambda idx=i: self.remove_stage(idx)).pack(side="left", padx=2)

    def edit_stage(self, index):
        line = self.extra_stages[index]
        StagePropertiesDialog(self, line, lambda res: self.update_stage(index, res))

    def update_stage(self, index, new_line):
        self.extra_stages[index] = new_line
        self.refresh_extra_stages()

    def remove_stage(self, index):
        del self.extra_stages[index]
        self.refresh_extra_stages()

    def select_slot(self, index):
        self.selected_slot_index = index
        if index < len(self.slots):
            slot = self.slots[index]
            if slot.get("type") == "slot":
                chars = slot.get("characters", [])
                char_names = [c["char"] for c in chars]
                self.status_bar.configure(text=f"Slot {index}: Slot Group [{len(chars)}] - {', '.join(char_names[:3])}...")
                self.param_entry.delete(0, "end")
            else:
                char = slot.get("char", "")
                self.status_bar.configure(text=f"Slot {index}: {char}")
                self.param_entry.delete(0, "end")
                self.param_entry.insert(0, slot.get("params", ""))
        else:
            self.status_bar.configure(text=f"Slot {index}: Empty")
            self.param_entry.delete(0, "end")

    def assign_char_to_slot(self, char_name):
        if self.selected_slot_index is None: return
        while len(self.slots) <= self.selected_slot_index: 
            self.slots.append({"type": "single", "char": "empty", "params": ""})
        self.slots[self.selected_slot_index] = {"type": "single", "char": char_name, "params": ""}
        self.refresh_grid()
        self.select_slot(self.selected_slot_index)

    def update_current_slot_params(self):
        if self.selected_slot_index is None: return
        if self.selected_slot_index < len(self.slots):
            slot = self.slots[self.selected_slot_index]
            if slot.get("type") != "slot":  # Only for single chars
                slot["params"] = self.param_entry.get()
                messagebox.showinfo("Success", "Updated")

    def show_context_menu(self, event, index):
        self.select_slot(index)
        menu = tk.Menu(self, tearoff=0)
        
        slot = self.slots[index] if index < len(self.slots) else None
        is_slot_group = slot and slot.get("type") == "slot"
        
        if is_slot_group:
            menu.add_command(label="Edit Slot Group...", command=lambda: self.open_slot_group_editor(index))
        else:
            menu.add_command(label="Properties...", command=lambda: self.open_properties(index))
            menu.add_command(label="Create Slot Group...", command=lambda: self.open_slot_group_editor(index))
        
        menu.add_separator()
        menu.add_command(label="Set Random", command=lambda: self.assign_char_to_slot("randomselect"))
        menu.add_command(label="Set Empty", command=lambda: self.assign_char_to_slot("empty"))
        if not is_slot_group:
            menu.add_command(label="Clear Params", command=lambda: self.update_current_slot_params())
        menu.tk_popup(event.x_root, event.y_root)

    def open_slot_group_editor(self, index):
        """Open the slot group editor dialog."""
        while len(self.slots) <= index:
            self.slots.append({"type": "single", "char": "empty", "params": ""})
        
        slot = self.slots[index]
        SlotGroupDialog(self, slot, self.available_chars, self.chars_dir, 
                       lambda res: self.on_slot_group_save(index, res))

    def on_slot_group_save(self, index, result):
        """Handle saving from slot group editor."""
        self.slots[index] = result
        self.refresh_grid()
        self.select_slot(index)

    def open_properties(self, index):
        if index >= len(self.slots): return
        slot = self.slots[index]
        if not slot["char"] or slot["char"].lower() in ["empty", "randomselect"]: return
        
        path = os.path.join(self.chars_dir, slot["char"])
        final = None
        if os.path.isdir(path):
            defi = os.path.join(path, os.path.basename(path)+".def")
            if os.path.exists(defi): final = defi
        elif os.path.exists(path): final = path
        elif os.path.exists(path+".def"): final = path+".def"
        else:
            std = os.path.join(self.chars_dir, slot["char"], slot["char"]+".def")
            if os.path.exists(std): final = std
            
        CharPropertiesDialog(self, slot["char"], final, slot["params"], lambda res: self.on_prop_save(index, res))

    def on_prop_save(self, index, res):
        self.slots[index]["params"] = res
        self.select_slot(index)

    def save_select_def(self):
        if not os.path.exists(self.data_dir): os.makedirs(self.data_dir)
        
        if self.config.getboolean("Options", "Backup", fallback=True):
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            bk = os.path.join(self.data_dir, "GoSelect_Backups", f"select_{ts}.def")
            if not os.path.exists(os.path.dirname(bk)): os.makedirs(os.path.dirname(bk))
            try: shutil.copy2(self.select_def_path, bk)
            except: pass
        
        with open(self.select_def_path, 'w', encoding='utf-8') as f:
            for l in self.sections["pre"]: f.write(l)
            
            for s in self.slots:
                if s.get("type") == "slot":
                    # Slot group - write as slot = { }
                    chars = s.get("characters", [])
                    if chars:
                        f.write("slot = {\n")
                        for char_data in chars:
                            char_name = char_data.get("char", "")
                            parts = [char_name]
                            if char_data.get("next"): parts.append(f"next = {char_data['next']}")
                            if char_data.get("previous"): parts.append(f"previous = {char_data['previous']}")
                            if char_data.get("select"): parts.append(f"select = {char_data['select']}")
                            f.write("  " + ", ".join(parts) + "\n")
                        f.write("}\n")
                else:
                    # Single character
                    c = s.get("char", "") or "empty"
                    line = c
                    if s.get("params"): line += f", {s['params']}"
                    f.write(line + "\n")
            
            for l in self.sections["mid"]: f.write(l) 
            for s in self.extra_stages: f.write(s+"\n")
            for l in self.sections["post"]: f.write(l)
            
        messagebox.showinfo("Saved", "File saved.")

    def open_options(self):
        OptionsDialog(self, self.config, lambda cfg: self.save_config())

if __name__ == "__main__":
    app = GOSelect()
    app.mainloop()
