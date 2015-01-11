# -*- coding: cp1252 -*-
form = """
    <form method = "/upload">
    <form>
    <label>
    Presenter Name
    <input type = "Text" name = “p_name”>
    </label>
    <br>
    <label>
    Email Address
    <input email=“p_email”>
    </label><br>
    <label>
    Presentation File
    <input type = file name="p_preso">
    </label><br>
    <input type = "Submit">
    </form>
"""

auth_code_form = """
    <form method=post>
        <label>Authorization Code<input type ="text" name = "code"></label>
        <br>
        <input type = "Submit>
    </form>"""

