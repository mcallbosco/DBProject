import flet as ft
from flet import TemplateRoute
import mysql.connector
import random
import os
import json

import math
import flet.map as map
import datetime
import time
showExampleStuff = False
doInitialFormatCheck = True

#It's definitly used for localizing and not for when we switch from this name
cName = "United Not States Postal Service"
cCode = "UNSPS"

weightUnit = "lb"
smallWeightUnit = "oz"
dimensionUnit = "in"
cubicDemensionUnit = "ft^3"
smallWeightConversion = 0.035274
cubicConversion = 0.0000353147
dimensionConversion = 0.393701

#load MYSQLCREDS.JSON file

if os.path.exists("MYSQLCREDS.JSON"):
    with open("MYSQLCREDS.JSON") as f:
        data = json.load(f)
        mydb = mysql.connector.connect(
            host=data["host"],
            port=data["port"],
            user= data["user"],
            password=data["password"],
        )
else:
    print("MYSQLCREDS.JSON file not found")
    print("Look at MYSQLCREDS.JSON for an example")
    exit()
    
mycursor = mydb.cursor(buffered=True,dictionary=True)
marker_layer_ref = ft.Ref[map.MarkerLayer]()
mycursor.execute("USE shipping")
mycursor.execute("SELECT * FROM status_info;")
status_info = mycursor.fetchall()
#set interactive_timeout and wait_timeout to a year
mycursor.execute("SET GLOBAL interactive_timeout = 31536000")
mycursor.execute("SET GLOBAL wait_timeout = 31536000")


connected = False

#tracking number specification
#first 10 digits are the package number
#Last 2 digits are the previous numbers added together
#The last 2 numbers are not stored in the database, they are only used to verify the number before checking serverside. 
#init sql connection

def main(page: ft.Page):
    global connected
    page.on_connect = lambda e: redo(page)
    redo(page)


def redo(page: ft.Page):
    page.navigation_bar = None
    
    page.clean()
    #close any open dialogs
    while page.overlay:
        page.overlay.clear()
    screenWidth = page.width
    global map_container
    
    page.title = "Tracking Updates"

    txt_number = ft.TextField(text_align=ft.TextAlign.RIGHT, width=100)

    def checkTracking(number):
        id = str(number)
        if len(number) == 12:
            if number[10:12] == str((int(id[0])+int(id[1])+int(id[2])+int(id[3])+int(id[4])+int(id[5])+int(id[6])+int(id[7])+int(id[8])+int(id[9]))).zfill(3)[1:3]:
                return True
        return False
    
    def displayIDProperly(id):
        return str(id) + str((int(id[0])+int(id[1])+int(id[2])+int(id[3])+int(id[4])+int(id[5])+int(id[6])+int(id[7])+int(id[8])+int(id[9]))).zfill(3)[1:3]
    
    
    
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
    packageDemensionValueCubic = ft.Text("", color=ft.Colors.GREY_900)
    packageWeightString = ft.Text("Package weight: ")
    packageWeightValue = ft.Text("")
    packageCreationDate = ft.Text("Label creation at: ")
    packageCreationDateValue = ft.Text("")
    packageDispatchDate = ft.Text("Dispatch date: ")
    packageDispatchDateValue = ft.Text("")
    insuredString = ft.Text("Insured: ")
    insuredValue = ft.Text("")
    packageDispatchRow = ft.Row([packageDispatchDate, packageDispatchDateValue], visible=False)

    searchResultsView2 = ft.Column(
        [
            ft.Row([trackingNumberString, trackingNumberValue]),\
            ft.Row([packageDemensionString, packageDemensionValue, packageDemensionValueCubic]),\
            ft.Row([packageWeightString, packageWeightValue]),\
            ft.Row([packageCreationDate, packageCreationDateValue]),\
            packageDispatchRow,\
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
        if not checkTracking(routeStripped) and doInitialFormatCheck or route.data == "/":
            return
        routeStripped = routeStripped[0:10]
        packageIDInternal = str(int(routeStripped))

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
                        ft.Text(statusResults[x["status"]-1]["name"] + " at \n" + prettyTime),
                        ft.Text("        " +location, expand=True)
                    ]),
                    content=ft.Column([ft.Text("Details: " + statusResults[x["status"]-1]["description"])]),
                ))
            HistoryView.visible = True

            searchResultsView.visible = True
            trackingNumberValue.value = displayIDProperly(routeStripped)
            packageDemensionValue.value = str(int(math.ceil(myresult[0]["length"])* dimensionConversion)) + "x" + str(int(math.ceil(myresult[0]["width"])* dimensionConversion)) + "x" + str(int(math.ceil(myresult[0]["height"])* dimensionConversion)) + dimensionUnit
            weightInOz = round(myresult[0]["weight"] * smallWeightConversion)
            if weightInOz < 16:
                packageWeightValue.value = str(weightInOz) + smallWeightUnit
            else:
                packageWeightValue.value = str(int(weightInOz/16)) + weightUnit + " " + str(math.ceil(weightInOz % 16)) + smallWeightUnit
            mycursor.execute(f"SELECT * FROM insurance WHERE id = {packageIDInternal};")
            insuranceInfo = mycursor.fetchall()
            if insuranceInfo:
                insuranceValue = insuranceInfo[0]["value_coverage"]
                insuredValue.value = "Yes, up to $" + str(insuranceValue)
            else:
                insuredValue.value = "No"
            prettyCreation = myresult[0]["time_created"].strftime("%m/%d/%Y, %H:%M:%S")
            if myresult[0]["time_of_dispatch"]:
                prettyDispatch = myresult[0]["time_of_dispatch"].strftime("%m/%d/%Y, %H:%M:%S")
            else:
                prettyDispatch = ""
                #for the days elapsed use  creation time - system time
            daydiff = (myresult[0]["time_created"] - datetime.datetime.now()).days
            if daydiff < 0:
                daydiff = 0
            shippingTime = myresult[0]["estimated_time_from_dispatch"]
            shippingTime =  shippingTime - daydiff
            if shippingTime < 0:
                shippingTime = 0
            daydiff = shippingTime

            
            progressBar.value = calculatePersentageBar(historyResults, daydiff, myresult[0]["estimated_time_from_dispatch"])
            if delivered:
                progressBar.value = 1
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
                    packageInProgressStatus.value = statusResults[historyResults[len(historyResults)-1]["status"]-1]["tense_name"]
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
                packageDispatchRow.visible = True
                packageDispatchDateValue.value = prettyDispatch
            else:
                packageDispatchRow.visible = False
            page.update()
        

    def checkCallback(e):
        if doInitialFormatCheck:
            if not checkTracking(txti_tracking.value):
                txti_tracking.border_color = ft.Colors.RED
                errorMessage.visible = True
                page.update()
                return
        #start sql query
        mycursor.execute("USE shipping")
        mycursor.execute("SELECT * FROM package WHERE id = " + str(int(txti_tracking.value))[0:10] + ";")
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

    
    def clearColor(e):
        if txti_tracking.border_color == ft.Colors.RED:
            txti_tracking.border_color = ft.Colors.GREY_500
            errorMessage.visible = False
            page.update()

    txti_tracking = ft.TextField(value="", text_align=ft.TextAlign.RIGHT, input_filter = ft.InputFilter('^[0-9]*$'), max_length=12, on_change=clearColor, on_submit=checkCallback)
    txti_tracking.width = page.width * 0.8
    but_check = ft.FilledTonalButton("Track")
    but_check.on_click = checkCallback
    errorMessage = ft.Text("Invalid tracking number", color=ft.Colors.RED, visible=False)
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
    
    loginButton = ft.FilledTonalButton("Login")
    loginButton.on_click = lambda e: spawnLogin(page)
    howToUseButton = ft.FilledTonalButton("How to use", url="https://github.com/mcallbosco/DBProject/blob/main/OnlineDemoREADME.md")


    #create a row with the login and how to use button, have the how to use align to the left and the login align to the right
    topButtonRow = ft.Row ([howToUseButton, loginButton], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    
    page.add(topButtonRow)
    page.add(searchBarView)
    page.add (progressBarView)
    page.add(beingDeliveredText)
    page.add(deliverdView)
    page.add(searchResultsView)
    page.add (HistoryView)
    page.on_route_change = route_change
    page.go(page.route)
    page.scroll = True
    txti_tracking.focus()

def displayIDProperly(id):
        return str(id) + str((int(id[0])+int(id[1])+int(id[2])+int(id[3])+int(id[4])+int(id[5])+int(id[6])+int(id[7])+int(id[8])+int(id[9]))).zfill(3)[1:3]

    
def spawnLogin(page: ft.Page):
    page.clean()
    page.scroll = False
    page.title = "Login"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    def login_click(e):
        valid = True
        typeOfUser = "Driver" #We will grab this from the user database if we end up doing that
        mycursor.execute(f"SELECT * FROM accounts WHERE username = '{txtf_username.value}'")
        user = mycursor.fetchone()
        if user == None:
            valid = False
        else:
            typeOfUser = user['roll']
        if valid:
            match typeOfUser:
                case "Manager":
                    #clear the page
                    page.remove(loginPage)
                    spawnManager(page, user)
                case "Driver":
                    page.remove(loginPage)
                    spawnDriver(page, user)
                case "Clerk":
                    page.remove(loginPage)
                    spawnClerk(page, user)
                case _:
                    txt_invalid.value = "Invalid Username or Password"
                    txtf_password.border_color = ft.Colors.RED
                    txtf_username.border_color = ft.Colors.RED
                    page.update()
        else:
            txt_invalid.value = "Invalid Username or Password"
            txtf_password.border_color = ft.Colors.RED
            txtf_username.border_color = ft.Colors.RED
            page.update()
    txtf_username = ft.TextField(text_align=ft.TextAlign.LEFT, width=300, on_submit=login_click)
    txtf_username.label = "Username"
    txtf_password = ft.TextField(text_align=ft.TextAlign.LEFT, width=300)
    txtf_password.label = "Password"
    txtf_password.password = True
    but_login = ft.FilledTonalButton("Login")
    image = ft.Image(src = f"/res/logoTemp.png")
    txt_invalid = ft.Text("   ", color=ft.Colors.RED)
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

    def textChange(e):
        if txt_invalid.value != "   ":
            txt_invalid.value = "   "
            txtf_password.border_color = ft.Colors.BLACK   
            txtf_username.border_color = ft.Colors.BLACK
            page.update()
    
    but_login.on_click = login_click
    txtf_username.on_change = textChange
    txtf_password.on_change = textChange
    page.add(
        loginPage
    )
    txtf_username.focus()

def spawnManager(page: ft.Page, user):
    page.scroll = True
    screenWidth = page.width
    #List of all packages in the facility. When a package is clicked on, there will be a popup with details, and the ability to assign a package to the driver with a destination facility.
    mycursor.execute(f"SELECT * FROM ready_for_assignment where location = {user['facility_id']}")
    packages = mycursor.fetchall()
    assignmentPanel = ft.Column()
    assignmentView = ft.Container(content=ft.ExpansionTile(
                    title=ft.Text("Sitting Packages"),
                    affinity=ft.TileAffinity.LEADING,
                    initially_expanded=True,
                    controls=[
                        assignmentPanel
                    ],
                    
                    expand=True, width=screenWidth * 0.7),expand=True, alignment=ft.alignment.center, visible=False)
    unassignmentPanel = ft.ExpansionPanelList(
        controls=[])
    unassignmentView = ft.Container(content=ft.ExpansionTile(
                    title=ft.Text("Sitting Packages"),
                    affinity=ft.TileAffinity.LEADING,
                    initially_expanded=False,
                    controls=[
                        assignmentPanel
                    ],
                    expand=True, width=screenWidth * 0.7),expand=True, alignment=ft.alignment.center, visible=False)
    listOfDrivers = []
    mycursor.execute(f"SELECT * FROM accounts WHERE roll = 'Driver' and facility_id = {user['facility_id']}")
    listOfDrivers = mycursor.fetchall()
    listOfLocations = []
    mycursor.execute(f"SELECT * FROM facilities")
    listOfLocations = mycursor.fetchall()
    listOfDriversDropDown = ft.Dropdown(on_change=lambda e: page.update())
    listOfDriversDropDown.label = "Driver"
    driverOptions = []
    for driver in listOfDrivers:
        driverOptions.append(ft.dropdown.Option(text=driver['username'], data=driver['id']))

    listOfDriversDropDown.options = driverOptions
    listOfDriversDropDown.value = driverOptions[0].data
    listOfLocationsDropDown = ft.Dropdown(on_change=lambda e: page.update())
    listOfLocationsDropDown.label = "Destination"
    locationOptions = []
    for location in listOfLocations:
        locationOptions.append(ft.dropdown.Option(text=location['name'], data=location['id']))
    listOfLocationsDropDown.options = locationOptions
    listOfLocationsDropDown.value = locationOptions[0].data

    def constructAddressString(address):
        addressString = ""
        #only use name, locality, administrative_area, postal_code
        if address['name_line'] != None:
            addressString += address['name_line'] + "\n"
        if address['locality'] != None:
            addressString += address['locality'] + ", "
        if address['administrative_area'] != None:
            addressString += address['administrative_area'] + " "
        if address['postal_code'] != None:
            addressString += address['postal_code']
        return addressString
    

    
    def assignPackage(e):
        selectedFacility = None
        for location in listOfLocations:
            if location['name'] == listOfLocationsDropDown.value:
                selectedFacility = location["id"]
        selectedUserID = ""
        for driver in listOfDrivers:
            if driver['username'] == listOfDriversDropDown.value:
                selectedUserID = driver["id"]

        if selectedFacility == None or selectedUserID == "":
            #popup to select a facility
            material_actions = [
                ft.TextButton(text="Close", on_click=lambda e: page.close(e.control.parent)),
                ]
            page.open(ft.AlertDialog(
                title=ft.Text("Error"),
                content=ft.Text("Please select a destination facility/driver."),
                actions=material_actions,
            ))
            return
        mycursor.execute(f"DELETE FROM ready_for_assignment WHERE package_id = {e.control.data}")
        mycursor.execute(f"INSERT INTO package_assignment (package_id, driver_id, from_facility_id, to_facility_id, status) VALUES ({e.control.data}, {selectedUserID}, {user['facility_id']}, {selectedFacility}, 1)")
        mydb.commit()
        mycursor.execute(f"UPDATE package SET time_of_dispatch = NOW() WHERE id = {e.control.data}")
        mydb.commit()
        for assignment in assignmentPanel.controls:
            if assignment.title.controls[0].value == str(displayIDProperly(str(e.control.data))):
                assignmentPanel.controls.remove(assignment)
        page.update()

    def spawnHistory(e):
        packageCounter = 0
        for package in packages:
            packageCounter += 1
            addressString = ""
            mycursor.execute(f"SELECT * FROM destination_address WHERE id = {package['package_id']}")
            address = mycursor.fetchone()
            addressString = constructAddressString(address)
            assignmentPanel.controls.append(ft.ExpansionTile(
                title=ft.Row([
                    ft.Text(str(displayIDProperly(str(package['package_id'])))),
                ]),
                controls=[ft.Column([ft.Text("Details: "), ft.Text(addressString), ft.Row([ft.Text("Driver: "), listOfDriversDropDown]), ft.Row([ft.Text("Destination: "), listOfLocationsDropDown]), ft.FilledTonalButton("Assign", on_click=assignPackage, data=package['package_id'])])],
            ))
        if packageCounter == 0:
            assignmentPanel.controls.append(ft.Text("No packages to assign."))
        assignmentView.visible = True
        page.update()

    page.add(assignmentView)
    spawnHistory(None)

def spawnDriver(page: ft.Page, user):
    page.scroll = True
    inTheMiddleOfSomething = False
    def constructAddressString(address):
            addressString = ""
            #only use name, locality, administrative_area, postal_code
            if address['name_line'] != None:
                addressString += address['name_line'] + "\n"
            if address['locality'] != None:
                addressString += address['locality'] + ", "
            if address['administrative_area'] != None:
                addressString += address['administrative_area'] + " "
            if address['postal_code'] != None:
                addressString += address['postal_code']
            return addressString
    def markAsDelivered(e, manualData = None):
                if manualData == None:
                    manualData = e.control.data
                mycursor.execute(f"SELECT * FROM package_assignment WHERE package_id = {manualData} and driver_id = {userID} and status = 2")
                assignmentDetails = mycursor.fetchone()
                mycursor.execute(f"SELECT * FROM package WHERE id = {manualData}")
                packageDetails = mycursor.fetchone()
                mycursor.execute(f"SELECT * FROM destination_address WHERE id = {manualData}")
                address = mycursor.fetchone()
                mycursor.execute(f"SELECT * FROM facilities WHERE id = {assignmentDetails['to_facility_id']}")
                destinationFacilityName = mycursor.fetchone()['name']

                def handle_delivery_conf(e):
                    if e.control.text == "Yes":
                        toFacilityID = assignmentDetails["to_facility_id"]
                        if toFacilityID == 0:
                            mycursor.execute("UPDATE package SET time_of_delivery = NOW() WHERE id = " + str(e.control.data))
                        else:
                            mycursor.execute(f"INSERT INTO ready_for_assignment (package_id, time_created, location) VALUES ({e.control.data}, NOW(), {toFacilityID})")
                        mycursor.execute(f"SELECT * FROM facilities WHERE id = {toFacilityID}")
                        facility = mycursor.fetchone()
                        status = facility["arrived_status_code"]
                        mycursor.execute(f"SELECT * FROM status_info WHERE id = {status}")
                        statusrow = mycursor.fetchone()
                        locationName = facility["name"]
                        if locationName == "Address":
                            locationName = "Listed Address"
                            
                        
                        mycursor.execute(f"Insert INTO package_status (package_id, status, time_created, location_x, location_y, location_name, location_id) VALUES ({e.control.data},{status}, NOW(), 0, 0, '{locationName}', {toFacilityID})")
                        mycursor.execute(f"UPDATE package_assignment SET status = 3 WHERE package_id = {e.control.data} and driver_id = {userID} and status = 2")
                        mydb.commit()
                    page.close(e.control.parent)
                    page.update()
                    if e.control.text == "Yes":
                        time.sleep(.2)
                        swapViews(1)
                yesbuttonforthing = ft.TextButton(text="Yes", on_click=handle_delivery_conf, data=manualData)

                #
                material_actions = [
                    ft.TextButton(text="No", on_click=handle_delivery_conf, data=manualData),
                    yesbuttonforthing,

                    ]
                page.open(ft.AlertDialog(
                        title=ft.Text("Confirm Delivery"),
                        content=ft.Text("Tracking number: " + displayIDProperly(str(manualData)) + "\n Package Address:\n" + constructAddressString(address) + "\n Destination Address:\n " + destinationFacilityName),
                        actions=material_actions,
                    ))
                yesbuttonforthing.focus()
    userID = user['id']

    def getLatestStatus(packageID):
        mycursor.execute(f"SELECT * FROM package_status WHERE package_id = {packageID} ORDER BY time_created DESC")
        return mycursor.fetchone()
    def markAllAsDelivered(e):
        def handle_mark_all(e):
            if e.control.text == "Yes":
                inTheMiddleOfSomething = True
                mycursor.execute(f"SELECT * FROM package_assignment WHERE driver_id = {userID} and status = 2")
                packagesToDeliver = mycursor.fetchall()
                page.close(e.control.parent)
                for package in packagesToDeliver:
                    markAsDelivered(None, manualData=package['package_id'])
                inTheMiddleOfSomething = False
                swapViews(1)
        #popup to confirm
        material_actions = [
        ft.TextButton(text="Yes", on_click=handle_mark_all),
        ft.TextButton(text="No", on_click=handle_mark_all),
        ]
        page.open(ft.AlertDialog(
            title=ft.Text("Mark all as delivered?"),
            content=ft.Text("Are you sure you want to mark all packages as delivered?"),
            actions=material_actions,
        ))
    

    def swapViews(e = None):
        if inTheMiddleOfSomething:
            return
        
        deliveryPanel = ft.ExpansionPanelList(controls=[])
        if e == None or e == 0:
            index = 0
        elif e == 1:
            index = 1
        else :
            index = e.control.selected_index
        #Logic for loading view
        if index == 0:

            mycursor.execute(f"SELECT * FROM package_assignment WHERE driver_id = {userID} and status = 1")
            page.clean()
            packagesAvaliableToDeliver = mycursor.fetchall()
            if len(packagesAvaliableToDeliver) == 0:
                page.add(ft.Text("You have no packages assigned to you."))
                page.update()
                return
            loadContainerContents = []
            checkboxes = []
            def loadMarkedPackages(e):
                for checkbox in checkboxes:
                    if checkbox.value:
                        mycursor.execute(f"SELECT * FROM package_assignment WHERE package_id = {checkbox.data}")
                        package = mycursor.fetchone()
                        mycursor.execute(f"SELECT * FROM package WHERE id = {checkbox.data}")
                        packageInfo = mycursor.fetchone()
                        if (package['to_facility_id'] == 0):
                            """Create Table package_status (
                                id INT PRIMARY KEY, 
                                package_id INT, 
                                status INT,
                                time_created TIMESTAMP,
                                location_x DECIMAL(6,4),
                                location_y DECIMAL(6,4),
                                location_name VARCHAR(255),
                                location_id INT
                            );"""
                            lastStatus = getLatestStatus(package['package_id'])
                            statusX = lastStatus['location_x']
                            statusY = lastStatus['location_y']
                            package_id = package['package_id']
                            location_name = lastStatus["location_name"]
                            mycursor.execute(f"INSERT INTO package_status (package_id, status, time_created, location_x, location_y, location_name, location_id) VALUES ({package_id}, 11, NOW(), {statusX}, {statusY}, '{location_name}', 0)")
                            mydb.commit()
                        else:
                            #left facility.
                            lastStatus = getLatestStatus(package['package_id'])
                            lastID = lastStatus['location_id']
                            mycursor.execute(f"SELECT * FROM facilities WHERE id = {package['from_facility_id']}")
                            facility = mycursor.fetchone()
                            nextStatus = facility["departed_status_code"]
                            mycursor.execute(f"INSERT INTO package_status (package_id, status, time_created, location_x, location_y, location_name, location_id) VALUES ({package['package_id']}, {nextStatus}, NOW(),0 , 0, '{facility["name"]}', {lastID})")
                            mydb.commit()
                        mycursor.execute(f"UPDATE package_assignment SET status = 2 WHERE package_id = {checkbox.data} and driver_id = {userID}")
                        mydb.commit()
                swapViews(0)
            for package in packagesAvaliableToDeliver:
                destinationSTR = ""
                if package['to_facility_id'] == 0:
                    destinationSTR = "Final Destination"
                else:
                    mycursor.execute(f"SELECT * FROM facilities WHERE id = {package['to_facility_id']}")
                    destinationSTR = mycursor.fetchone()['name']
                checkboxes.append(ft.Checkbox(label=displayIDProperly(str(package['package_id'])) + "     Destination: " + destinationSTR, data=package['package_id']))
            loadContainerContents.append(ft.Column(checkboxes))
            loadContainerContents.append(ft.FilledTonalButton("Load", on_click=loadMarkedPackages))
            page.add(ft.Column(loadContainerContents))
            page.update()
        #Logic for delivery view
        else:
            def unload(e):
                #get arrival for current facility
                mycursor.execute(f"SELECT * FROM facilities WHERE id = {user['facility_id']}")
                facility = mycursor.fetchone()
                arrivedStatus = facility['arrived_status_code']
                facilityName = facility['name']
                mycursor.execute(f"UPDATE package_assignment SET status = 1 WHERE package_id = {e.control.data} and driver_id = {userID} and status = 2")
                mycursor.execute(f"INSERT INTO package_status (package_id, status, time_created, location_x, location_y, location_name, location_id) VALUES ({e.control.data}, {arrivedStatus}, NOW(), 0, 0, \"{facilityName}\", {user['facility_id']})")
                mydb.commit()
                swapViews(1)
            
            page.clean()
            mycursor.execute(f"SELECT * FROM package_assignment WHERE driver_id = {userID} and status = 2")
            packagesToDeliver = mycursor.fetchall()
            if len(packagesToDeliver) == 0:
                page.add(ft.Text("You have not loaded any packages.\n Please select the load tab to load packages to deliver."))
                page.update()
                return
            
            for package in packagesToDeliver:
                 addressToWrite = ""
                 if (package['to_facility_id'] != 0):
                    mycursor.execute(f"SELECT * from facilities WHERE id = {package['to_facility_id']}")
                    facility = mycursor.fetchone()
                    mycursor.execute(f"SELECT * FROM destination_address WHERE id = {facility['address_id']}")
                    address = mycursor.fetchone()
                    addressToWrite = constructAddressString(address)
                 else:
                    mycursor.execute(f"SELECT * FROM destination_address WHERE id = {package['package_id']}")
                    addressToWrite = constructAddressString(mycursor.fetchone())
                 deliveryPanel.controls.append(ft.ExpansionPanel(
                    header=ft.Row([
                        ft.Text(str(displayIDProperly(str(package['package_id'])))),
                    ]),
                    can_tap_header=True,
                    content=ft.Column([ft.Text("Deliver to: "), ft.Text(addressToWrite), ft.Button("Mark as delivered", data=package['package_id'], on_click=markAsDelivered), ft.Button("Unload", on_click = unload, data=package['package_id'])]),
                ))
            
           
            page.add(deliveryPanel)
            #on click bring up a popup to confirm and then call the function
            page.add(ft.FilledTonalButton("Mark all as delivered", on_click=markAllAsDelivered))
            page.update()
            
        page.update()
    page.title = "CupertinoNavigationBar Example"
    page.navigation_bar = ft.CupertinoNavigationBar(
        bgcolor=ft.Colors.AMBER_100,
        inactive_color=ft.Colors.GREY,
        active_color=ft.Colors.BLACK,
        on_change=swapViews,
        destinations=[
            ft.NavigationBarDestination(icon=ft.icons.FRONT_LOADER, label="Load"),
            ft.NavigationBarDestination(icon=ft.Icons.COMMUTE, label="Deliver"),
        ]
    )


    #load container will be a list of packages that need to be loaded, check boxes to select them, and a button to confirm
    swapViews()

def spawnClerk(page: ft.Page, user):
    page.scroll = True
    userLocationID = user['facility_id']
    #get facility info
    mycursor.execute(f"SELECT * FROM facilities WHERE id = {userLocationID}")
    facility = mycursor.fetchone()

    #page to enter in package info. 
    """CREATE TABLE package (
    id INT PRIMARY KEY,
    width INT,    -- In centimeters
    length INT,     -- In centimeters
    height INT,   -- In centimeters
    weight INT,  -- In grams
    price DECIMAL(10, 2),  -- In dollars
    type INT,
    insurance_id INT,
    shipment_id INT,
    estimated_distance INT,
    estimated_time_from_dispatch INT,
    time_created TIMESTAMP,
    time_updated TIMESTAMP,
    time_of_dispatch TIMESTAMP,
    time_of_delivery TIMESTAMP,
    delivery_cordinates_x DECIMAL(6,4),
    delivery_cordinates_y DECIMAL(6,4),
    delivery_conformation VARCHAR(255)
    );"""
    """Create Table destination_address (
    id INT PRIMARY KEY,
    country VARCHAR(2),
    name_line VARCHAR(255),
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    organisation_name VARCHAR(255),
    administrative_area VARCHAR(50),
    sub_administrative_area VARCHAR(50),
    locality VARCHAR(50),
    dependent_locality VARCHAR(50),
    postal_code VARCHAR(50),
    thoroughfare VARCHAR(255),
    premise VARCHAR(255),
    sub_premise VARCHAR(255)
    );"""
    page.title = "Clerk"
    def generateInsuranceTypeString(insuranceType):
        return insuranceType['name'] + "\n" + "Max Coverage: $" + str(insuranceType['max_coverage'])
    def generateid():
        mycursor.execute("SELECT MAX(id) FROM package")
        return mycursor.fetchone()['MAX(id)'] + 1
    def displayIDProperly(id):
        return str(id) + str((int(id[0])+int(id[1])+int(id[2])+int(id[3])+int(id[4])+int(id[5])+int(id[6])+int(id[7])+int(id[8])+int(id[9]))).zfill(3)[1:3]
    #get insurance types from insuranceType
    mycursor.execute("SELECT * FROM insurance_type")
    insuranceTypes = mycursor.fetchall()
    insuranceTypeOptions = []
    insuranceDropDown = ft.Dropdown()
    insuranceDropDown.label = "Insurance Type"
    insuranceTypeOptions.append(ft.dropdown.Option(text="None", data=0))
    for insuranceType in insuranceTypes:
        insuranceTypeOptions.append(ft.dropdown.Option(text=generateInsuranceTypeString(insuranceType), data=insuranceType['id']))
    dimensionTypeOptions = []
    dimensionDropDown = ft.Dropdown(width=60)
    dimensionDropDown.label = "unit"
    dimensionTypeOptions.append(ft.dropdown.Option(text="IN", data=2.54, key=0))
    dimensionTypeOptions.append(ft.dropdown.Option(text="FT", data=30.48, key=1))
    dimensionTypeOptions.append(ft.dropdown.Option(text="CM", data=1, key=2))
    lengthKey = {"0": "2.54", "1": "30.48", "2": "1"}
    dimensionDropDown.options = dimensionTypeOptions
    dimensionDropDown.value = 0


    #get shipment types from shipmentType
    mycursor.execute("SELECT * FROM shipment_type")
    shipmentTypes = mycursor.fetchall()
    shipmentTypeOptions = []
    shipmentDropDown = ft.Dropdown()
    shipmentDropDown.label = "Shipment Type"
    for shipmentType in shipmentTypes:
        shipmentTypeOptions.append(ft.dropdown.Option(text=shipmentType['name'], data=shipmentType['id']))
    shipmentDropDown.options = shipmentTypeOptions
    insuranceDropDown.options = insuranceTypeOptions
    packageWidthString = ft.Text("Dimensions: ")
    packageDimensionsSeperator = ft.Text(" x ")
    packageWidthField = ft.TextField(label="W", width=80,input_filter = ft.InputFilter('^[0-9]*$'), max_length=3)
    packageLengthField = ft.TextField(label="L", width=80,input_filter = ft.InputFilter('^[0-9]*$'), max_length=3)
    packageHeightField = ft.TextField(label="H", width=80,input_filter = ft.InputFilter('^[0-9]*$'), max_length=3)
    
    packageWeightString = ft.Text("Weight: ")
    packageWeightField = ft.TextField(input_filter = ft.InputFilter('^[0-9]*$'), max_length=5, width=80)
    packageWeightUnit = ft.Text("oz")
    packageInsuranceString = ft.Text("Insurance Type: ")
    packageInsuranceField = insuranceDropDown
    packageShipmentString = ft.Text("Shipment Type: ")
    packageShipmentField = shipmentDropDown

    packageFirstNameString = ft.Text("First Name: ")
    packageFirstNameField = ft.TextField(max_length=50)
    packageLastNameString = ft.Text("Last Name: ")
    packageLastNameField = ft.TextField(max_length=50)
    packageOrganisationString = ft.Text("Organisation: ")
    packageOrganisationField = ft.TextField(max_length=255)
    packageAdminAreaString = ft.Text("Administrative Area: ")
    packageAdminAreaField = ft.TextField(max_length=50)
    packageLocalityString = ft.Text("Locality: ")
    packageLocalityField = ft.TextField(max_length=50)
    packagePostalCodeString = ft.Text("Postal Code: ")
    packagePostalCodeField = ft.TextField(max_length=50)
    packageThoroughfareString = ft.Text("Thoroughfare: ")
    packageThoroughfareField = ft.TextField(max_length=255)
    packagePremiseString = ft.Text("Premise: ")
    packagePremiseField = ft.TextField(max_length=255)
    packageCountryString = ft.Text("Country: ")
    packageCountryField = ft.TextField(max_length = 2)
    packageDeclaredValueString = ft.Text("Declared Value: ")
    packageDeclaredValueField = ft.TextField(input_filter=ft.InputFilter('^[0-9]*$'), max_length=10)
    def initilizeFields(event):
        packageWidthField.focus()
        packageWidthField.value = ""
        packageLengthField.value = ""
        packageHeightField.value = ""
        packageWeightField.value = ""
        packageInsuranceField.value = "None"
        packageShipmentField.value = ""
        packageFirstNameField.value = ""
        packageLastNameField.value = ""
        packageOrganisationField.value = ""
        packageAdminAreaField.value = ""
        packageLocalityField.value = ""
        packagePostalCodeField.value = ""
        packageThoroughfareField.value = ""
        packagePremiseField.value = ""
        packageCountryField.value = ""
        packageDeclaredValueField.value = ""
        page.update()
    def addPackageTransaction(event):
        
        calculatedDistance = 1500
        id = generateid()
        shipmentCost = 0
        shipmentTypeID = 0 
        shipmentID = packageShipmentField.value
        shipmentETA = 0
        for shipmentType in shipmentTypes:
            if shipmentType['name'] == shipmentID:
                shipmentTypeID = shipmentType['id']
                shipmentETA = float(shipmentType['days_per500Miles']) * (calculatedDistance/500)
                shipmentCost = shipmentType['cost_per500Miles']
        width = float(packageWidthField.value) * float(lengthKey[str(dimensionDropDown.value)])
        length = float(packageLengthField.value) * float(lengthKey[str(dimensionDropDown.value)])
        height = float(packageHeightField.value) * float(lengthKey[str(dimensionDropDown.value)])
        weight = float(packageWeightField.value) * 28.3495
        insuranceID = packageInsuranceField.value
        insuranceIDFinal = 0
        insuranceRow = None
        insuranceCost = 0
        for insuranceType in insuranceTypes:
            if generateInsuranceTypeString(insuranceType) == insuranceID:
                insuranceIDFinal = insuranceType['id']
                insuranceRow = insuranceType


        
        if insuranceIDFinal != 0:
            insuranceCost = float(insuranceRow['cost_per500Miles']) * (calculatedDistance/500)

        shipmentID = packageShipmentField.value
        firstName = packageFirstNameField.value
        lastName = packageLastNameField.value
        organisation = packageOrganisationField.value
        adminArea = packageAdminAreaField.value
        locality = packageLocalityField.value
        postalCode = packagePostalCodeField.value
        thoroughfare = packageThoroughfareField.value
        premise = packagePremiseField.value
        country = packageCountryField.value
        declaredValue = packageDeclaredValueField.value
        mycursor.execute(f"INSERT INTO package (id, width, length, height, weight, price, type, insurance_id, shipment_id, estimated_distance, estimated_time_from_dispatch, time_created, time_updated, delivery_cordinates_x, delivery_cordinates_y, delivery_conformation) VALUES ({id}, {width}, {length},  {height}, {weight}, {shipmentCost}, 0, NULL, {shipmentTypeID}, {calculatedDistance}, {shipmentETA} , NOW(), NOW(), 42.4532, -79.3407, '')")
        
        mycursor.execute(f"INSERT INTO destination_address (id, country, name_line, first_name, last_name, organisation_name, administrative_area, locality, postal_code, thoroughfare, premise) VALUES ({id}, '{country}', '{firstName} {lastName}', '{firstName}', '{lastName}', '{organisation}', '{adminArea}', '{locality}', '{postalCode}', '{thoroughfare}', '{premise}')")
        if insuranceIDFinal != 0:
            mycursor.execute(f"INSERT INTO insurance (id, type, price, value_coverage) VALUES ({id}, {insuranceIDFinal}, {insuranceCost}, {declaredValue})")
        
        mycursor.execute(f"INSERT INTO package_status (package_id, status, time_created, location_x, location_y, location_name, location_id) VALUES ({id}, 1, NOW(), 0, 0, \"{facility["name"]}\", {user["facility_id"]})")
        mycursor.execute(f"INSERT INTO ready_for_assignment (package_id, time_created, location) VALUES ({id}, NOW(), {user["facility_id"]})")
        mydb.commit()
        page.close(event.control.parent)
        #popup with tracking number
        def okayAction(e):
            page.close(e.control.parent)
            initilizeFields(None)
        closeButton = ft.TextButton(text="OK", on_click=okayAction)
        material_actions = [
            closeButton, ft.TextButton(text="Copy Tracking Number", on_click=lambda e: page.set_clipboard(displayIDProperly(str(id)))),
            ]
        page.open(ft.AlertDialog(
            title=ft.Text("Package Added"),
            content=ft.Text("Tracking Number: " + displayIDProperly(str(id))),
            actions=material_actions,
            on_dismiss=initilizeFields,
        ))
        closeButton.focus()
    def generateEstimate(event):
        #check that all boxes are filled that are required
        if packageWidthField.value == "" or packageLengthField.value == "" or packageHeightField.value == "" or packageWeightField.value == "" or packageShipmentField.value == "" or packageFirstNameField.value == "" or packageLastNameField.value == "" or packageAdminAreaField.value == "" or packageLocalityField.value == "" or packagePostalCodeField.value == "" or packageThoroughfareField.value == "" or packageCountryField.value == "":
            material_actions = [
                ft.TextButton(text="Close", on_click=lambda e: page.close(e.control.parent)),
                ]
            page.open(ft.AlertDialog(
                title=ft.Text("Error"),
                content=ft.Text("Please fill out all required fields."),
                actions=material_actions,
            ))
            return
        calculatedDistance = 1500 #this would be calculated based on address and route, but it is out of scope. 
        #put a popup with estimated distance, estimated insurance cost, estimated shipment cost, total cost and estimated time. 
        #get the insurance cost
        insuranceCost = 0
        insuranceID = packageInsuranceField.value
        for insuranceType in insuranceTypes:
            if generateInsuranceTypeString(insuranceType) == insuranceID:
                insuranceCost = float(insuranceType['cost_per500Miles']) * (calculatedDistance/500)
        #get the shipment cost
        shipmentCost = 0
        shipmentID = packageShipmentField.value
        for shipmentType in shipmentTypes:
            if shipmentType['name'] == shipmentID:
                shipmentCost = float(shipmentType['cost_per500Miles']) * (calculatedDistance/500)

        
        #get the total cost
        totalCost = insuranceCost + shipmentCost
        #get the estimated time
        estimatedTime = 0
        for shipmentType in shipmentTypes:
            if shipmentType['name'] == shipmentID:
                estimatedTime = float(shipmentType['days_per500Miles']) * (calculatedDistance/500)

        if estimatedTime == 0:
            estimatedTime = 1
        #put a popup with estimated distance, estimated insurance cost, estimated shipment cost, total cost and estimated time.
        processButton = ft.TextButton(text="Process", on_click=addPackageTransaction)
        material_actions = [
            ft.TextButton(text="Cancel", on_click=lambda e: page.close(e.control.parent)),
            processButton,
        ]
        page.open(ft.AlertDialog(
            title=ft.Text("Estimated Costs"),
            content=ft.Text(f"Estimated Distance: {calculatedDistance:.2f} miles\nEstimated Insurance Cost: ${insuranceCost:.2f}\nEstimated Shipment Cost: ${shipmentCost:.2f}\nTotal Cost: ${totalCost:.2f}\nEstimated Time: {estimatedTime} days"),
            actions=material_actions,
        ))
        processButton.focus()
    def checkAdditionalOptions(event):
        if packageInsuranceField.value != "None" or None:
            #make sure there's a declared value
            if packageDeclaredValueField.value == "":
                material_actions = [
                    ft.TextButton(text="Close", on_click=spawnAdditionalOptions),
                    ]
                page.open(ft.AlertDialog(
                    title=ft.Text("Error"),
                    content=ft.Text("Please enter a declared value."),
                    actions=material_actions,
                ))
                return
        page.close(event.control.parent)
    def spawnAdditionalOptions(event):
        #popup with insurance options
        material_actions = [
            ft.TextButton(text="Close", on_click=checkAdditionalOptions ),
            ]
        page.open(ft.AlertDialog(
            title=ft.Text("Additional Options"),
            content=ft.Column([ft.Text("Insurance Options"), packageInsuranceField, ft.Text("Declared Value"), packageDeclaredValueField]),
            actions=material_actions,
        ))





    packageProcessButton = ft.FilledTonalButton("Estimate", on_click=generateEstimate)
    additionalInfoButton = ft.FilledTonalButton("Additional Options", on_click=spawnAdditionalOptions)


    inputContainer = ft.Column(
        [
            ft.Row([ft.Text(" ")]),
            ft.Row([packageWidthString, packageWidthField, packageDimensionsSeperator, packageLengthField, packageDimensionsSeperator, packageHeightField, dimensionDropDown]),
            ft.Row([packageWeightString, packageWeightField, packageWeightUnit]),
            ft.Row([packageShipmentString, packageShipmentField]),
            ft.Row([packageFirstNameString, packageFirstNameField]),
            ft.Row([packageLastNameString, packageLastNameField]),
            ft.Row([packageOrganisationString, packageOrganisationField]),
            ft.Row([packageAdminAreaString, packageAdminAreaField]),
            ft.Row([packageLocalityString, packageLocalityField]),
            ft.Row([packagePostalCodeString, packagePostalCodeField]),
            ft.Row([packageThoroughfareString, packageThoroughfareField]),
            ft.Row([packagePremiseString, packagePremiseField]),
            ft.Row([packageCountryString, packageCountryField]),\
            additionalInfoButton,
            packageProcessButton
        ],
    )
    page.add(inputContainer)
    initilizeFields(None)

ft.app(main, view = ft.AppView.WEB_BROWSER)