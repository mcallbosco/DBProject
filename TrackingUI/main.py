import flet as ft
from flet import TemplateRoute
import mysql.connector
import random
import math
showExampleStuff = False
doInitialFormatCheck = False

weightUnit = "lb"
smallWeightUnit = "oz"
dimensionUnit = "in"
cubicDemensionUnit = "ft^3"
smallWeightConversion = 0.035274
cubicConversion = 0.0000353147
dimensionConversion = 0.393701

mydb = mysql.connector.connect(
        host="localhost",
        port="3307",
        user= "root",
        password="RaNSEneyHYrO",
    )
mycursor = mydb.cursor(buffered=True)
#tracking number specification
#first 10 digits are the package number
#Last 2 digits are the previous numbers added together
#The last 2 numbers are not stored in the database, they are only used to verify the number before checking serverside. 
#init sql connection


def main(page: ft.Page):
    
    page.title = "Flet counter example"

    txt_number = ft.TextField(text_align=ft.TextAlign.RIGHT, width=100)
    

    def checkTracking(number):
        if len(number) == 12:
            if number[10:12] == str(sum([int(x) for x in number[:-2]])):
                return True
        return False
    
    #fun strings
    trackingNumberString = ft.Text("Tracking number: ")
    trackingNumberValue = ft.Text("")
    packageDemensionString = ft.Text("Package demensions: ")
    packageDemensionValue = ft.Text("")
    packageDemensionValueCubic = ft.Text("", color=ft.colors.GREY_900)
    packageWeightString = ft.Text("Package weight: ")
    packageWeightValue = ft.Text("")
    searchResultsView2 = ft.Column(
        [
            ft.Row([trackingNumberString, trackingNumberValue]),\
            ft.Row([packageDemensionString, packageDemensionValue, packageDemensionValueCubic]),\
            ft.Row([packageWeightString, packageWeightValue])
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        visible=True
    )

    searchResultsView = ft.ExpansionTile(
                    title=ft.Text("Package Info" ),
                    affinity=ft.TileAffinity.LEADING,
                    initially_expanded=False,
                    controls=[
                        searchResultsView2
                    ],
                    visible=False
                )
    

    def route_change(route):
        #checks
        routeStripped = route.data[1:]
        print (route.data)
        if not checkTracking(routeStripped) and doInitialFormatCheck or route.data == "/":
            return
        
        mycursor.execute("USE shipping")
        mycursor.execute("SELECT * FROM package WHERE id = " + str(int(routeStripped)) + ";")
        myresult = mycursor.fetchall()
        if len(myresult) == 0:
            page.go("/")
        else:
            searchResultsView.visible = True
            trackingNumberValue.value = routeStripped
            packageDemensionValue.value = str(int(math.ceil(myresult[0][1])* dimensionConversion)) + "x" + str(int(math.ceil(myresult[0][2])* dimensionConversion)) + "x" + str(int(math.ceil(myresult[0][3])* dimensionConversion)) + dimensionUnit
            weightInOz = myresult[0][4] * smallWeightConversion
            if weightInOz < 16:
                packageWeightValue.value = str(weightInOz) + smallWeightUnit
            else:
                packageWeightValue.value = str(int(weightInOz/16)) + weightUnit + " " + str(math.ceil(weightInOz % 16)) + smallWeightUnit



            page.update()
        

    def checkCallback(e):
        if doInitialFormatCheck:
            if not checkTracking(txti_tracking.value):
                txti_tracking.border_color = ft.colors.RED
                errorMessage.visible = True
                page.update()
                return
        #start sql query
        mycursor.execute("USE shipping")
        mycursor.execute("SELECT * FROM package WHERE id = " + str(int(txti_tracking.value)) + ";")
        myresult = mycursor.fetchall()
        if len(myresult) == 0:
            errorMessage.visible = True
            page.update()
            return
            
        page.go("/" + txti_tracking.value)
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


        
    
    searchBarView = ft.Container(
        content= ft.Column([ft.Row(
        [
            txti_tracking,
            but_check
        ],
        
        

    ),ft.Row([errorMessage, ft.Text("")])],
    alignment= ft.MainAxisAlignment.CENTER
    ), padding=ft.padding.only(top=80),alignment= ft.alignment.center)
    

    page.add(searchBarView)
    page.add(searchResultsView)
    page.on_route_change = route_change
    page.go(page.route)

ft.app(main)