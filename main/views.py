from django.shortcuts import render, redirect
from .models import Project
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout, authenticate, login
from django.contrib import messages
from .forms import NewUserForm, AddressInputForm
from selenium import webdriver
from pandas import read_csv
from math import cos, asin, sqrt, floor
import numpy as np


# Create your views here.
def homepage(request):
    return render(
        request = request, template_name='main/home.html',
        context={'projects':Project.objects.all()}
    )

def register(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            login(request, user)
            messages.success(request, f"New account created: {username}")
            return redirect("main:homepage")

        else:
            for msg in form.error_messages:
                messages.error(request, f"{msg}: {form.error_messages[msg]}")

            return render(request = request,
                          template_name = "main/register.html",
                          context={"form":form})

    form = NewUserForm
    return render(request = request,
                  template_name = "main/register.html",
                  context={"form":form})

def logout_request(request):
    logout(request)
    messages.info(request, "Logged out successfully!")
    return redirect("main:homepage")

def login_request(request):
    if request.method == 'POST':
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}")
                return redirect('main:homepage')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    form = AuthenticationForm()
    return render(request=request,
                  template_name="main/login.html",
                  context={"form":form})

def print_request(request):


    form = AddressInputForm(request.POST)
    if form.is_valid():
        try:
            address_number = int(form.cleaned_data['address_count'])
            vehicle_count = int(form.cleaned_data['vehicle_count'])
        except ValueError:
            messages.error(request, "Please enter a valid number of addresses")
            return render(request, "main/adro_input.html", context={"form": form})

        address_string = form.cleaned_data['address_string'].split("%")

        def minIgnoringZero(incomingArray):
            minValue = 99999999999
            minKey = 0
            for i in range(len(incomingArray)):
                if incomingArray[i] < minValue and incomingArray[i] != 0:
                    minValue = incomingArray[i]
                    minKey = i
            return minKey, minValue

        def settingColumn(twoDArray, colIndex, targetValue):
            for i in twoDArray:
                i[colIndex] = targetValue

            return twoDArray

        def getCoordinatesFromCsv(incomingDocument):
            # df = read_csv(incomingDocument)
            # one = df['Header'].to_list()
            """Please add functionality to the things up above"""

            one = [j for i in incomingDocument for j in i]

            driver = webdriver.Chrome()
            url = "https://geocoder.ca/"

            coords = {}

            for i in range(len(one)):
                driver.get(url)
                elem = driver.find_element_by_class_name('input-block-level')
                elem.clear()
                elem.send_keys(one[i])

                second = driver.find_element_by_xpath('//*[@id="geocode"]/input[2]')
                second.click()
                last = driver.find_element_by_xpath('/html/body/div[2]/table[2]/tbody/tr/td[2]/p/strong').get_attribute(
                    'innerHTML')
                coords[one[i]] = [float(j) for j in last.split(", ")]
            driver.quit()
            return coords

        # print(getCoordinatesFromCsv("waterlooWebScrapingTest.csv"))

        def distance(lat1, lon1, lat2, lon2):
            p = 0.017453292519943295  # Pi/180
            a = 0.5 - cos((lat2 - lat1) * p) / 2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
            return 12742 * asin(sqrt(a))  # 2*R*asin...

        def distanceMatrix(coords):

            distMatrix = np.zeros((len(coords), len(coords)))
            """Iterate over each location in the dictionary to create corresponding rows of the distance matrix."""
            outerPointer = 0
            for i in coords:

                innerPointer = 0
                for j in coords:
                    if i == j:
                        distMatrix[outerPointer][innerPointer] = 0
                    else:
                        distMatrix[outerPointer][innerPointer] = distance(lat1=coords[i][0], lon1=coords[i][1],
                                                                          lat2=coords[j][0], lon2=coords[j][1])
                    innerPointer = innerPointer + 1
                outerPointer = outerPointer + 1

            return distMatrix, list(coords.keys())

        def tabuSearch(numVehicles, depotLocation, distanceMatrix):
            distancesToDepot = [i[depotLocation] for i in distanceMatrix]
            distanceMatrix = settingColumn(twoDArray=distanceMatrix, colIndex=depotLocation, targetValue=9999999)
            pointerStorage = [[depotLocation] for _ in range(numVehicles)]
            totalDistanceStorage = [0 for i in range(numVehicles)]
            for i in range(len(distanceMatrix) - 1):
                currentAgent = i % numVehicles
                closestCity, minForAgent = minIgnoringZero(distanceMatrix[pointerStorage[currentAgent][-1]])

                pointerStorage[currentAgent].append(closestCity)
                distanceMatrix = settingColumn(twoDArray=distanceMatrix, colIndex=closestCity, targetValue=9999999)
                totalDistanceStorage[currentAgent] += minForAgent

            totalDistanceStorage = [totalDistanceStorage[i] + distancesToDepot[pointerStorage[i][-1]] for i in
                                    range(len(totalDistanceStorage))]
            pointerStorage = [i + [0] for i in pointerStorage]

            return pointerStorage, totalDistanceStorage

        def routeVisualization(pointerStorage, totalDistanceStorage, locationAddresses):
            driver = webdriver.Chrome()
            urls = []
            current_vehicle = 0

            for vehicles in pointerStorage:
                mapURL = "https://www.google.ca/maps/dir/"
                for locations in vehicles:
                    paddedLocation = locationAddresses[locations].replace(" ", "+") + "/"
                    mapURL += paddedLocation

                driver.execute_script("window.open('about:blank', 'tab{}');".format(str(current_vehicle)))
                driver.switch_to.window("tab{}".format(str(current_vehicle)))
                driver.get(mapURL)

                urls.append(mapURL)
                current_vehicle += 1

            print("The drivers covered {} respectively".format(totalDistanceStorage))
            return urls

        globalDistanceMatrix, allAddresses = distanceMatrix(getCoordinatesFromCsv([address_string]))

        vehilcesVisited, allDistances = tabuSearch(vehicle_count, 0, globalDistanceMatrix)

        urls = routeVisualization(pointerStorage=vehilcesVisited, totalDistanceStorage=allDistances,
                                  locationAddresses=allAddresses)
        for i in range(len(urls)):
            messages.error(request, "We have completed the calculations for vehilce # {}. You can view the results here: {}".format(i, urls[i]))
    return render(request, "main/adro_input.html", context={"form":form})



