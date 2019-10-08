# Keypirinha: a fast launcher for Windows (keypirinha.com)
# Credits https://github.com/ueffel wrote the majority of the code

import keypirinha as kp
import subprocess
import urllib
import keypirinha_util as kpu

class recoll(kp.Plugin):

    CONFIG_SECTION_MAIN = "main"
    DEFAULT_FILE_PATH = "C:\\Program Files (x86)\\Recoll\\recoll.exe"
    DEFAULT_COMMANDS = "-t"
    
    # Variables
    file_path = DEFAULT_FILE_PATH
    commands = DEFAULT_COMMANDS
    
    def __init__(self):
        super().__init__()
        self._debug = False
        self.dbg("CONSTRUCTOR")
        
    def on_start(self):
        self.dbg("On Start")
        self._read_config()

    def on_catalog(self):
        self.set_catalog([
            self.create_item(
                category=kp.ItemCategory.KEYWORD,
                label="Recoll",
                short_desc="Queries the recoll index",
                target="recoll",
                args_hint=kp.ItemArgsHint.REQUIRED,
                hit_hint=kp.ItemHitHint.KEEPALL
            )
        ])

    def on_suggest(self, user_input, items_chain):
        if not items_chain or not user_input:
            return

        # avoid flooding if user still typing
        if self.should_terminate(0.250):
            return

        suggestions = []

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        output, err = subprocess.Popen([self.file_path,
                                    self.commands.strip(),
                                    user_input],
                                    stdout=subprocess.PIPE,
                                    shell=False,
                                    startupinfo=startupinfo).communicate()
        if err:
            self.err(err)
        output_str = output.decode("utf-8")
        self.dbg("Commands: {}".format(self.commands.strip()))
        self.dbg("Input: {}".format(user_input))
        self.dbg(output_str)

        idx = 0
        for line in output_str.splitlines():
            if idx < 2:
                idx += 1
                continue
            fields = line.split("\t")
            file = fields[1][1:-1]
            text = fields[2][1:-1]

            suggestions.append(self.create_item(
                category=kp.ItemCategory.REFERENCE,
                label=text,
                short_desc=urllib.parse.unquote(file)[8:],
                target=str(idx),
                data_bag=str(file),
                args_hint=kp.ItemArgsHint.FORBIDDEN,
                hit_hint=kp.ItemHitHint.KEEPALL
            ))

            # limit to 100 results
            if idx > 100:
                break
            idx += 1

        self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

    def on_execute(self, item, action):
        file = item.data_bag()
        #os.startfile(urllib.parse.unquote(file)[8:])
        kpu.shell_execute(file)

    def _read_config(self):
        self.dbg("Read Config")

        settings = self.load_settings()
        self.file_path = settings.get(
            "file_path",
            self.CONFIG_SECTION_MAIN,
            self.DEFAULT_FILE_PATH)
        self.dbg("Loaded file_path: {}".format(self.file_path))
        
        # TODO: use more cmd options from ini file
        self.commands = settings.get(
            "commands",
            self.CONFIG_SECTION_MAIN,
            self.DEFAULT_COMMANDS)

        if self.commands.find(self.DEFAULT_COMMANDS) == -1:
            self.commands = self.DEFAULT_COMMANDS+" "+self.commands
            
        self.dbg("Loaded commands: {}".format(self.commands))