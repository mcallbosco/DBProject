import flet as ft
from flet import TemplateRoute


#tracking number specification
#first 10 digits are the package number
#Last 2 digits are the previous numbers added together
#The last 2 numbers are not stored in the database, they are only used to verify the number before checking serverside. 

def main(page: ft.Page):
    page.title = "Flet counter example"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    txt_number = ft.TextField(value="0", text_align=ft.TextAlign.RIGHT, width=100)
    

    def checkTracking(number):
        if len(number) == 12:
            if number[:-2] == str(sum([int(x) for x in number[:-2]])):
                return True
        return False
    
    searchResultsView = ft.Column(
        [
            ft.Text("Tracking number: " + txt_number.value),
            ft.Text("Valid: " + str(checkTracking(txt_number.value)))
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )

    def route_change(route):
        troute = TemplateRoute(page.route)
        

    def checkCallback(e):
        page.go(txt_number.value)

    


    txti_tracking = ft.TextField(value="0", text_align=ft.TextAlign.RIGHT)
    txti_tracking.width = page.width * 0.8
    but_check = ft.FilledTonalButton("Track")
    but_check.on_click = checkCallback
    
    searchBarView = ft.Row(
        [
            txti_tracking,
            but_check
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )
    page.add(searchBarView)
    page.on_route_change = route_change
    page.go(page.route)

ft.app(main)