import flet as ft
from flet import TemplateRoute
import mysql.connector
import random
from geopy.geocoders import Nominatim

import math
import flet.map as map
import datetime
showExampleStuff = False
doInitialFormatCheck = False

weightUnit = "lb"
smallWeightUnit = "oz"
dimensionUnit = "in"
cubicDemensionUnit = "ft^3"
smallWeightConversion = 0.035274
cubicConversion = 0.0000353147
dimensionConversion = 0.393701
geolocator = Nominatim(user_agent="geoapiExercises")

mydb = mysql.connector.connect(
        host="localhost",
        port="3307",
        user= "root",
        password="RaNSEneyHYrO",
    )
mycursor = mydb.cursor(buffered=True,dictionary=True)
marker_layer_ref = ft.Ref[map.MarkerLayer]()
mycursor.execute("USE shipping")
mycursor.execute("SELECT * FROM status_info;")
status_info = mycursor.fetchall()

#tracking number specification
#first 10 digits are the package number
#Last 2 digits are the previous numbers added together
#The last 2 numbers are not stored in the database, they are only used to verify the number before checking serverside. 
#init sql connection


def main(page: ft.Page):
    screenWidth = page.width
    global map_container
    
    page.title = "Flet counter example"

    txt_number = ft.TextField(text_align=ft.TextAlign.RIGHT, width=100)

    def checkTracking(number):
        if len(number) == 12:
            if number[10:12] == str(sum([int(x) for x in number[:-2]])):
                return True
        return False
    
    
    
    map_container = ft.Container(
        
        height=400,
        width=600,
    )
    
    #fun strings
    packageHasBeenDelivered = ft.Text("Your package has been delivered on ")
    packageDeliveryDate = ft.Text("")
    packageDeliveryType = ft.Text("")
    packageInProgress = ft.Text("Your package ")
    packageInProgressStatus = ft.Text("")
    packageInProgressTime = ft.Text("It on track to arrive ", visible=False)
    packageInProgressLate = ft.Text("is currently running late. The ETA is unknown. It is", visible=False)
    packageInProgressTimeValue = ft.Text("")
    
    
    trackingNumberString = ft.Text("Tracking number: ")
    trackingNumberValue = ft.Text("")
    packageDemensionString = ft.Text("Package demensions: ")
    packageDemensionValue = ft.Text("")
    packageDemensionValueCubic = ft.Text("", color=ft.colors.GREY_900)
    packageWeightString = ft.Text("Package weight: ")
    packageWeightValue = ft.Text("")
    packageCreationDate = ft.Text("Label creation at: ")
    packageCreationDateValue = ft.Text("")
    packageDispatchDate = ft.Text("Dispatch date: ")
    packageDispatchDateValue = ft.Text("")
    insuredString = ft.Text("Insured: ")
    insuredValue = ft.Text("")

    searchResultsView2 = ft.Column(
        [
            ft.Row([trackingNumberString, trackingNumberValue]),\
            ft.Row([packageDemensionString, packageDemensionValue, packageDemensionValueCubic]),\
            ft.Row([packageWeightString, packageWeightValue]),\
            ft.Row([packageCreationDate, packageCreationDateValue]),\
            ft.Row([packageDispatchDate, packageDispatchDateValue]),\
            ft.Row([insuredString, insuredValue])

        ],
        alignment=ft.MainAxisAlignment.CENTER,
        visible=True
    )
    deliverdView = ft.Container(
        expand=True,
        content=ft.Row(
        controls=[
            ft.Column([packageHasBeenDelivered, packageDeliveryDate
            ,packageDeliveryType]),
            map_container

        ],
        alignment=ft.MainAxisAlignment.CENTER, wrap=True
        
    ), alignment=ft.alignment.center,visible=False)
    searchResultsView = ft.Container(content=ft.ExpansionTile(
                    title=ft.Text("Package Info"),
                    affinity=ft.TileAffinity.LEADING,
                    initially_expanded=False,
                    controls=[
                        searchResultsView2
                    ],
                    
                    width=screenWidth * 0.7
                ), expand=True, alignment=ft.alignment.center, visible=False)
    historyPanel = ft.ExpansionPanelList(
        controls=[])
    HistoryView = ft.Container(content=ft.ExpansionTile(
                    title=ft.Text("Delivery History" ),
                    affinity=ft.TileAffinity.LEADING,
                    initially_expanded=False,
                    controls=[
                        historyPanel
                    ],
                    
                    expand=True, width=screenWidth * 0.7),expand=True, alignment=ft.alignment.center, visible=False)
    
    progressBar = ft.ProgressBar(
        value=0.5,
        width=screenWidth * 0.8,
        height=20,
    )
    progressBarView = ft.Container(
        content=ft.Column([progressBar]),
        visible=False,
        alignment=ft.alignment.center
    )

    beingDeliveredText = ft.Container(
        content=ft.Column([
            ft.Row(
                [packageInProgress, packageInProgressLate, packageInProgressStatus],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=0
            ),
            ft.Row(
                [packageInProgressTime, packageInProgressTimeValue],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=0
            )
        ], 
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        visible=False,
        alignment=ft.alignment.center,
        expand=True
    )
    def calculatePersentageBar(routeProgress, daysElapsed, estimatedDays):
        if daysElapsed > estimatedDays:
            return 75*.01
        latestValue = 0
        for x in range(len(routeProgress)-1, -1, -1):
            tempstatus = status_info[routeProgress[x]["status"]]["progress_bar_percentage"] 
            if tempstatus:
                latestValue = tempstatus
                break
            if tempstatus == 0:
                latestValue = 0
                break
        if latestValue == 25:
            return (25+ (daysElapsed/estimatedDays) * 50) *.01
        else:
            return latestValue * .01

            

    def route_change(route):
        global map_container
        #checks
        routeStripped = route.data[1:]
        print (route.data)
        if not checkTracking(routeStripped) and doInitialFormatCheck or route.data == "/":
            return
        

        mycursor.execute("SELECT * FROM package WHERE id = " + str(int(routeStripped)) + ";")
        myresult = mycursor.fetchall()
        if len(myresult) == 0:
            page.go("/")
        else:
            progressBarView.visible = True
            delivered = myresult[0]["time_of_delivery"]
            #history logic
            mycursor.execute("SELECT * FROM status_info;")
            statusResults = mycursor.fetchall()
            mycursor.execute("SELECT * FROM package_status WHERE package_id = " + str(int(routeStripped)) + ";")
            historyResults = mycursor.fetchall()
            historyPanel.controls.clear()
            for x in historyResults:
                prettyTime = x["time_created"].strftime("%m/%d/%Y, %H:%M:%S")
                if not x["location_name"]:
                    location = "Location: Unknown"
                else:
                    location = "Location: \n" + x["location_name"]
                historyPanel.controls.append(ft.ExpansionPanel(
                    header=ft.Row([
                        ft.Text(statusResults[x["status"]]["name"] + " at \n" + prettyTime),
                        ft.Text("        " +location, expand=True)
                    ]),
                    content=ft.Column([ft.Text("Details: " + statusResults[x["status"]]["description"])]),
                ))
            HistoryView.visible = True

            searchResultsView.visible = True
            trackingNumberValue.value = routeStripped
            packageDemensionValue.value = str(int(math.ceil(myresult[0]["length"])* dimensionConversion)) + "x" + str(int(math.ceil(myresult[0]["width"])* dimensionConversion)) + "x" + str(int(math.ceil(myresult[0]["height"])* dimensionConversion)) + dimensionUnit
            weightInOz = myresult[0]["weight"] * smallWeightConversion
            if weightInOz < 16:
                packageWeightValue.value = str(weightInOz) + smallWeightUnit
            else:
                packageWeightValue.value = str(int(weightInOz/16)) + weightUnit + " " + str(math.ceil(weightInOz % 16)) + smallWeightUnit
            insuranceInfo = insurance_info = myresult[0]["insurance_id"]
            if insuranceInfo:
                mycursor.execute("SELECT * FROM insurance WHERE id = " + str(insuranceInfo) + ";")
                insuranceResult = mycursor.fetchall()
                insuranceValue = insuranceResult[0]["value_coverage"]
                insuredValue.value = "Yes, up to $" + str(insuranceValue)
            else:
                insuredValue.value = "No"
            prettyCreation = myresult[0]["time_created"].strftime("%m/%d/%Y, %H:%M:%S")
            if myresult[0]["time_of_dispatch"]:
                prettyDispatch = myresult[0]["time_of_dispatch"].strftime("%m/%d/%Y, %H:%M:%S")
            else:
                prettyDispatch = ""
                #for the days elapsed use  creation time - system time
            daydiff = (myresult[0]["time_created"] - datetime.datetime.now()).days + 1
            
            if daydiff < 0:
                daydiff = 0
            print (historyResults)
            progressBar.value = calculatePersentageBar(historyResults, daydiff, myresult[0]["estimated_time_from_dispatch"])
            if delivered:
                beingDeliveredText.visible = False
                prettyDelivery = delivered.strftime("%m/%d/%Y, %H:%M:%S")
                packageDeliveryDate.value = prettyDelivery
                packageDeliveryX = float(myresult[0]["delivery_cordinates_x"])
                packageDeliveryY = float(myresult[0]["delivery_cordinates_y"])
                maps = map.Map(
                    expand=True,
                    initial_center=map.MapLatitudeLongitude(packageDeliveryX, packageDeliveryY),
                    initial_zoom=18,
                    interaction_configuration=map.MapInteractionConfiguration(
                        flags=map.MapInteractiveFlag.ALL
                    ),
                    layers=[
                        map.TileLayer(
                            url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                        ),
                        map.MarkerLayer(ref=marker_layer_ref, markers=[]),
                    ],
                )
                map_container.content = maps
                packageDeliveryType.value = myresult[0]["delivery_conformation"]
                marker_layer_ref.current.markers.clear()
                marker_layer_ref.current.markers.append(
                map.Marker(
                    content=ft.Icon(
                        ft.Icons.LOCATION_ON, color=ft.cupertino_colors.DESTRUCTIVE_RED
                    ),
                    coordinates=map.MapLatitudeLongitude(packageDeliveryX, packageDeliveryY),
                    )
                 )
                             
                
                deliverdView.visible = True
            else:
                packageInProgressTime.visible = False
                packageInProgressLate.visible = False
                packageInProgressTimeValue.visible = False
                deliverdView.visible = False
                beingDeliveredText.visible = True
                if len(historyResults) == 0:
                    packageInProgressStatus.value = "has been created"
                else:
                    packageInProgressStatus.value = statusResults[historyResults[len(historyResults)-1]["status"]]["tense_name"]
                if daydiff < 0:
                    packageInProgressLate.visible = True
                    packageInProgressTime.visible = False
                    packageInProgressTimeValue.visible = False
                else:
                    packageInProgressTime.visible = True
                    packageInProgressTimeValue.visible = True
                    if daydiff == 0:
                        packageInProgressTimeValue.value = "today"
                    else:
                        packageInProgressTimeValue.value = "in "+ str(daydiff) + " days"


            packageCreationDateValue.value = prettyCreation
            if prettyDispatch != "":
                packageDispatchDateValue.visible = True
                packageDispatchDateValue.value = prettyDispatch
            else:
                packageDispatchDateValue.visible = False
            


            

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

    


    txti_tracking = ft.TextField(value="", text_align=ft.TextAlign.RIGHT)
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
        ],alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([errorMessage, ft.Text("")])],), 
        padding=ft.padding.only(top=80),
        alignment= ft.alignment.center, expand=True)
    
    

    page.add(searchBarView)
    page.add (progressBarView)
    page.add(beingDeliveredText)
    page.add(deliverdView)
    page.add(searchResultsView)
    page.add (HistoryView)
    page.on_route_change = route_change
    page.go(page.route)
    page.scroll = True

ft.app(main, view = ft.AppView.WEB_BROWSER)