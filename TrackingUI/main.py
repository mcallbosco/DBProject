import flet as ft
from flet import TemplateRoute

showExampleStuff = True
#tracking number specification
#first 10 digits are the package number
#Last 2 digits are the previous numbers added together
#The last 2 numbers are not stored in the database, they are only used to verify the number before checking serverside. 

def main(page: ft.Page):
    
    page.title = "Flet counter example"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    txt_number = ft.TextField(text_align=ft.TextAlign.RIGHT, width=100)
    

    def checkTracking(number):
        if len(number) == 12:
            if number[10:12] == str(sum([int(x) for x in number[:-2]])):
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
        doInitialFormatCheck = True

        if doInitialFormatCheck:
            if not checkTracking(txti_tracking.value):
                txti_tracking.border_color = ft.colors.RED
                errorMessage.visible = True
                page.update()
                return
            
        page.go(txt_number.value)
        page.update()
        #set page title
        page.title = "Tracking Number: " + txti_tracking.value
        page.update()

    


    txti_tracking = ft.TextField(value="0", text_align=ft.TextAlign.RIGHT)
    txti_tracking.width = page.width * 0.8
    but_check = ft.FilledTonalButton("Track")
    but_check.on_click = checkCallback
    errorMessage = ft.Text("Invalid tracking number", color=ft.colors.RED, visible=False)
    if showExampleStuff:
        text = ft.Text("Tracking number: 123456789045")
        page.add(text)
    
    searchBarView = ft.Column([ft.Row(
        [
            txti_tracking,
            but_check
        ],
        alignment=ft.MainAxisAlignment.CENTER
    ),ft.Row([errorMessage, ft.Text("")])])
    page.add(searchBarView)
    page.on_route_change = route_change
    page.go(page.route)

ft.app(main)