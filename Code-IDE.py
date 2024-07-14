import keyword
import re
import subprocess
from tkinter import *
from tkinter import messagebox
from tkinter.filedialog import asksaveasfilename, askopenfilename
from tkinter import ttk
from ttkwidgets.autocomplete import AutocompleteEntry

file_path = ''
current_language = 'Python'

languages_keywords = {
    'Python': keyword.kwlist,
    'C': ['auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do', 'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if', 'inline', 'int', 'long', 'register', 'restrict', 'return', 'short', 'signed', 'sizeof', 'static', 'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while', '_Alignas', '_Alignof', '_Atomic', '_Bool', '_Complex', '_Generic', '_Imaginary', '_Noreturn', '_Static_assert', '_Thread_local'],
    'Java': ['abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch', 'char', 'class', 'const', 'continue', 'default', 'do', 'double', 'else', 'enum', 'extends', 'final', 'finally', 'float', 'for', 'goto', 'if', 'implements', 'import', 'instanceof', 'int', 'interface', 'long', 'native', 'new', 'null', 'package', 'private', 'protected', 'public', 'return', 'short', 'static', 'strictfp', 'super', 'switch', 'synchronized', 'this', 'throw', 'throws', 'transient', 'try', 'void', 'volatile', 'while']
}

def format_c_code(code):
    lines = code.split('\n')
    formatted_code = []
    indent_level = 0
    indent_space = '    '  # You can adjust the number of spaces for each indentation level

    for line in lines:
        stripped_line = line.strip()
        
        # Check if the line is a preprocessor directive
        if stripped_line.startswith('#'):
            formatted_code.append(stripped_line)
            continue
        
        # Adjust indent level if the line contains closing braces at the beginning
        while stripped_line.startswith('}'):
            indent_level -= 1
            stripped_line = stripped_line[1:].strip()
        
        # Format the line with the current indentation level
        formatted_line = indent_space * indent_level + stripped_line
        formatted_code.append(formatted_line)
        
        # Adjust indent level if the line contains opening braces at the end
        if stripped_line.endswith('{'):
            indent_level += 1
    
    return '\n'.join(formatted_code)

def get_words(event):
    editor.tag_remove("found", "1.0", "end")
    editor.tag_remove("quoted_text", "1.0", "end")
    editor.tag_remove("character", "1.0", "end")
    editor.tag_remove("italic", "1.0", "end")
    editor.tag_remove("after_dot", "1.0", "end")

    text = editor.get("1.0", "end-1c")
    words = text.split()
    keywords_list = languages_keywords[current_language]

    for i in words:
        if i in keywords_list:
            search_word = i
            pattern = r"\b" + re.escape(search_word) + r"\b"
            for match in re.finditer(pattern, editor.get("1.0", "end"), re.IGNORECASE):
                start_index = match.start()
                end_index = match.end()
                editor.tag_add("found", f"1.0+{start_index}c", f"1.0+{end_index}c")

    characters_to_recolor = [':', ',', '(', ')', '{', '}', '[', ']', ';']
    for char in characters_to_recolor:
        start_index = "1.0"
        while True:
            start_index = editor.search(char, start_index, stopindex="end", nocase=True, exact=False)
            if not start_index:
                break
            end_index = editor.index(f"{start_index}+1c")
            editor.tag_add("character", start_index, end_index)
            start_index = end_index

    double_quotes_pattern = r'"([^"]*)"'
    for match in re.finditer(double_quotes_pattern, editor.get("1.0", "end")):
        start_index = match.start(1)
        end_index = match.end(1)
        editor.tag_add("quoted_text", f"1.0+{start_index}c", f"1.0+{end_index}c")

    single_quotes_pattern = r"'([^']*)'"
    for match in re.finditer(single_quotes_pattern, editor.get("1.0", "end")):
        start_index = match.start(1)
        end_index = match.end(1)
        editor.tag_add("quoted_text", f"1.0+{start_index}c", f"1.0+{end_index}c")

    content = editor.get("1.0", "end")
    start_index = "1.0"
    while True:
        start_index = editor.search("#", start_index, stopindex="end", nocase=True, exact=False)
        if not start_index:
            break
        end_index = editor.search("\n", start_index, stopindex="end", exact=True)
        editor.tag_add("italic", start_index, end_index)
        start_index = end_index

    recolor_after_dot(1)

def equalsymbol(event):
    start_index = "1.0"
    while True:
        start_index = editor.search("=", start_index, stopindex="end", nocase=True, exact=True)
        if not start_index:
            break
        end_index = f"{start_index}+1c"
        editor.tag_add("found", start_index, end_index)
        start_index = end_index

def set_file_path(path):
    global file_path
    file_path = path

def open_file(event=1):
    path = askopenfilename(filetypes=[('Python Files', '*.py'), ('C Files', '*.c'), ('Java Files', '*.java')])
    with open(path, 'r') as file:
        code = file.read()
        editor.delete('1.0', END)
        editor.insert('1.0', code)
        set_file_path(path)
        compiler.title(path + ' New IDE')
        code1 = editor.get('1.0', END)
        if code1 == code:
            compiler.title(path + ' New IDE')
        else:
            compiler.title('*' + path + ' New IDE')
    get_words(1)
    update_line_numbers(1)

def save_as(event=1):
    if file_path == '':
        file_type = [('Python Files', '*.py')]
        if current_language == 'C':
            file_type = [('C Files', '*.c')]
        elif current_language == 'Java':
            file_type = [('Java Files', '*.java')]
        path = asksaveasfilename(filetypes=file_type)
        compiler.title("Untitled")
    else:
        path = file_path
    with open(path, 'w') as file:
        code = editor.get('1.0', END)
        file.write(code)
        set_file_path(path)
        compiler.title(path + ' New IDE')

def update_line_numbers(event):
    line_numbers.config(state="normal")
    line_numbers.delete("1.0", "end")
    num_lines = editor.index("end-1c").split(".")[0]
    for i in range(1, int(num_lines) + 1):
        line_numbers.insert("end", f" {i}\n")
    line_numbers.config(state="disabled")

def recolor_after_dot(event=None):
    pattern = r"\.\s*([a-zA-Z0-9_]+)"
    text = editor.get("1.0", "end")
    matches = re.finditer(pattern, text)
    for match in matches:
        start_index = f"1.0+{match.start(1)}c"
        end_index = f"1.0+{match.end(1)}c"
        editor.tag_add("after_dot", start_index, end_index)

def run(event=1):
    c2 = Tk()
    c2.title("Output Window")
    code_output = Text(c2, height=10, bg="#292C34", fg="#CACACA", borderwidth=0, font=('Droid Sans Mono', 18), highlightbackground="#2e3138")
    code_output.pack(fill="both", expand=True)
    if file_path == '':
        messagebox.showwarning("Warning", "File Not Saved")
        return
    command = ''
    if current_language == 'Python':
        command = f'python {file_path}'
    elif current_language == 'C':
        executable_path = file_path.replace('.c', '')
        compile_command = f'gcc {file_path} -o {executable_path}'
        subprocess.call(compile_command, shell=True)
        command = executable_path
    elif current_language == 'Java':
        compile_command = f'javac {file_path}'
        subprocess.call(compile_command, shell=True)
        class_name = file_path.split('/')[-1].replace('.java', '')
        command = f'java {class_name}'
    
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    code_output.insert('1.0', output)
    if error != '':
        k = 1.0 + float(len(error) / 10)
        code_output.insert('1.0', error)
        code_output.tag_add("start", '1.0', str(k))
        code_output.tag_configure("start", foreground="red")

def on_scroll(*args):
    line_numbers.yview(*args)
    editor.yview(*args)

def exits(event=1):
    if file_path == '':
        ch = messagebox.askquestion("Warning", "Are you sure to quit")
        if ch == "yes":
            exit()

def set_language(event=None):
    global current_language
    current_language = language_var.get()
    get_words(None)

def format_code(event=1):
    if current_language == 'C':
        code = editor.get("1.0", END)
        formatted_code = format_c_code(code)
        editor.delete("1.0", END)
        editor.insert("1.0", formatted_code)
        get_words(None)

compiler = Tk()
compiler.title('Untitled New IDE')

menu_bar = Menu(compiler)
file_menu = Menu(menu_bar, tearoff=0)
file_menu.add_command(label='Open', command=open_file, accelerator="Ctrl+O")
compiler.bind('<Control-x>', exits)
compiler.bind('<Control-Shift-s>', save_as)
compiler.bind('<Control-s>', save_as)
compiler.bind('<Control-o>', open_file)
compiler.bind('<F5>', run)
file_menu.add_command(label='Save', command=save_as, accelerator="Ctrl+S")
file_menu.add_command(label='Save As', command=save_as, accelerator="Ctrl+Shift+S")
file_menu.add_command(label='Exit', command=exits, accelerator="Ctrl+Shift+S")
menu_bar.add_cascade(label='File', menu=file_menu)

run_bar = Menu(menu_bar, tearoff=0)
run_bar.add_command(label='Run', command=run, accelerator="F5")
menu_bar.add_cascade(label='Run', menu=run_bar)

language_var = StringVar()
language_var.set("Python")
language_menu = Menu(menu_bar, tearoff=0)
language_menu.add_radiobutton(label="Python", variable=language_var, value="Python", command=set_language)
language_menu.add_radiobutton(label="C", variable=language_var, value="C", command=set_language)
language_menu.add_radiobutton(label="Java", variable=language_var, value="Java", command=set_language)
menu_bar.add_cascade(label='Language', menu=language_menu)

format_menu = Menu(menu_bar, tearoff=0)
format_menu.add_command(label='Format C Code', command=format_code, accelerator="Ctrl+Shift+F")
menu_bar.add_cascade(label='Format', menu=format_menu)
compiler.bind('<Control-Shift-f>', format_code)

compiler.config(menu=menu_bar)

frame = Frame(compiler)
frame.pack(fill="both", expand=True)
ks = Scrollbar(frame)
ks.pack(side="right", fill="y")

line_numbers = Text(frame, width=4, bg="#23262b", fg="#919399", state="disabled", font=('Droid Sans Mono', 12), borderwidth=0, highlightbackground="#3D4048", yscrollcommand=ks.set)
line_numbers.pack(side="left", fill="y", expand=False)
line_numbers.tag_configure("S.no", justify="center")

editor = Text(frame, wrap="word", bg="#292C34", fg="#CACACA", borderwidth=0, undo=True, yscrollcommand=ks.set)
editor.configure(insertbackground='#CACACA', font=('Droid Sans Mono', 12))
editor.pack(side="left", fill="both", expand=True)
editor.bind("<space>", get_words)
editor.bind("<Tab>", get_words)
editor.bind("<Return>", get_words)
editor.bind("<Key>", equalsymbol)
editor.bind("<KeyRelease>", update_line_numbers)
editor.tag_configure("found", foreground="#C678DD")
editor.tag_configure("quoted_text", foreground="#8CB272")
editor.tag_configure("character", foreground="gold")
editor.tag_configure("after_dot", foreground="#5284AF")
editor.bind("<KeyPress>", recolor_after_dot)
ks.config(command=on_scroll)
editor.tag_configure("italic", font=('Droid Sans Mono', 12, "italic"), foreground="gray")

compiler.mainloop()
