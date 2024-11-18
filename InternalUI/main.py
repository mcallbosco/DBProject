import flet as ft

#It's definitly used for localizing and not for when we switch from this name
cName = "United Not States Postal Service"
cCode = "UNSPS"

def main(page: ft.Page):
    page.title = cCode + "Login"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    spawnLogin(page)

    

    
def spawnLogin(page: ft.Page):
    txtf_username = ft.TextField(text_align=ft.TextAlign.LEFT, width=300)
    txtf_username.label = "Username"
    txtf_password = ft.TextField(text_align=ft.TextAlign.LEFT, width=300)
    txtf_password.label = "Password"
    txtf_password.password = True
    but_login = ft.FilledTonalButton("Login")
    image = ft.Image(src = f"/res/logoTemp.png")
    txt_invalid = ft.Text("   ", color=ft.colors.RED)
    loginPage = ft.Column(
            [
                image,
                txtf_username,
                txtf_password,
                txt_invalid,
                ft.Row(
                [but_login],
                alignment=ft.MainAxisAlignment.END,
                width=300 
            )
            ],
            alignment=ft.MainAxisAlignment.CENTER,

        )
    def login_click(e):
        valid = False
        typeOfUser = "Clerk" #We will grab this from the user database if we end up doing that
        print("Username: " + txtf_username.value)
        print("Password: " + txtf_password.value)
        if valid:
            match typeOfUser:
                case "Manager":
                    #clear the page
                    page.remove(loginPage)
                    spawnManager(page)
                case "Driver":
                    page.remove(loginPage)
                    spawnDriver(page)
                case "Clerk":
                    page.remove(loginPage)
                    spawnClerk(page)
                case _:
                    print("Unimplimented user type")
        else:
            txt_invalid.value = "Invalid Username or Password"
            txtf_password.border_color = ft.colors.RED
            txtf_username.border_color = ft.colors.RED
            page.update()

    def textChange(e):
        if txt_invalid.value != "   ":
            txt_invalid.value = "   "
            txtf_password.border_color = ft.colors.BLACK   
            txtf_username.border_color = ft.colors.BLACK
            page.update()
    
    but_login.on_click = login_click
    txtf_username.on_change = textChange
    txtf_password.on_change = textChange
    page.add(
        loginPage
    )

def spawnManager(page: ft.Page):
    pass

def spawnDriver(page: ft.Page):
    pass

def spawnClerk(page: ft.Page):
    pass

    
        


ft.app(main)