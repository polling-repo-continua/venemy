import requests
import argparse
import json
import time
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning
import imghdr  # used for checking image file types
import os  # used for interacting with filesystem
import datetime

# Script Arguments
parser = argparse.ArgumentParser(description="Venemy: An Intel Tool For Venmo - Use at your own risk")
parser.add_argument('-u', '--user', required=False, help='Single username to research')
parser.add_argument('-c', '--crawl', required=False, help='Crawl depth of friends', action='store_true')
parser.add_argument('-f', '--format', required=False, help='Data Output Format. Choices are json,rdf,csv')
parser.add_argument('-bf', '--bruteForceFile', required=False, help="File with [user]names to brute force")
parser.add_argument('-bu', '--bruteForceUser', required=False, help="Single username to brute force")
parser.add_argument('-o', '--output', required=False, help="Output data to csv", action='store_true')
# parser.add_argument('-d', '--dir',required=False,help="Create directory for run")
# parser.add_argument('-a', '--auth',required=False,help="Authenticated Mode - Requires Valid Session Credentials")
args = parser.parse_args()

'''Venmo API Endpoints
https://api.venmo.com/v1/users/user_name - Endpoint for basic user information
https://venmo.com/api/v5/public - Endpoint for all public Venmo transactions
'''

'''
To-Do:
? Build larger picture function
- Write Authenticated Function
? Build depth crawler function
- Write to csv file for uuuuurrrrrrything
- Need to develop error handling for private profiles
- Need to add transaction function
'''

month = {
    'January': "01",
    'February': "02",
    'March': "03",
    'April': "04",
    'May': "05",
    'June': "06",
    'July': "07",
    'August': "08",
    'September': "09",
    'October': "10",
    'November': "11",
    'December': "12"
}

dayName = {
	'Monday':0,
	'Tuesday':1,
	'Wednesday':2,
	'Thursday':3,
	'Friday':4,
	'Saturday':5,
	'Sunday':6
}


# Setting up and Making the Web Call
def GetDataFromVenmo(url):
    try:
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:63.0) Gecko/20100101 Firefox/66.0'
        headers = {'User-Agent': user_agent}
        # Make web request for that URL and don't verify SSL/TLS certs
        response = requests.get(url, headers=headers, verify=False)
        return response

    except Exception as e:
        print('[!]   ERROR - Venmo issue: {}'.format(str(e)))
        exit(1)


# Grab data for a known user
def GetUserData(passed_user):
    # Parsing user information
    user = []
    url = 'https://api.venmo.com/v1/users/{}'.format(passed_user)
    print("\n[+] USER DATA: Requesting {}".format(url))
    resp = GetDataFromVenmo(url)
    data = resp.json()
    user.append(data['data']['username'])
    user.append(data['data']['display_name'])
    user.append(data['data']['first_name'])
    user.append(data['data']['last_name'])
    user.append(data['data']['friends_count'])
    user.append(data['data']['profile_picture_url'].replace("square", "normal"))
    if "venmopics" in data['data']['profile_picture_url'] or "facebook" in data['data']['profile_picture_url']:
        pic = data['data']['profile_picture_url']
        get_profile_pic(pic, data['data']['username'])
    user.append(data['data']['id'])
    user.append(data['data']['date_joined'])
    fb_id = GetFbId(user[5])
    user.append(fb_id)
    if user:
        return user


# Grab the User's Transactions - API access for this is restricted
def GetUserTransactions(passed_user):
    transaction = {"friends": [], "details": []}
    url = 'https://venmo.com/{}'.format(passed_user)
    print("\n[+] TRANSACTION DATA: Requesting {}".format(url))
    resp = GetDataFromVenmo(url)
    html_doc = BeautifulSoup(resp.text, "html.parser")
    sm = html_doc.find_all('div', class_='paymentpage-payment-container')
    for i in sm:
        data = GetTransactionDetails(i, passed_user)
        for f in data["friend"]:
            if f not in transaction["friends"]:
                transaction["friends"].append(f)
        transaction["details"].append(data["details"])
    return transaction


def GetTransactionDetails(html_doc, passed_user):
    data = {"friend": [], "details": {}}
    names = html_doc.find('div', 'paymentpage-subline').find_all('a', href=True)

    data["details"]["donor_username"] = names[0]["href"]
    data["details"]["donor_name"] = names[0].text
    data["details"]["recipient_username"] = names[1]["href"]
    data["details"]["recipient_name"] = names[1].text

    if passed_user not in data["details"]["donor_username"]:
        data["friend"].append(data["details"]["donor_username"])
    else:
        data["friend"].append(data["details"]["recipient_username"])

    data["details"]["text"] = html_doc.find('div', 'paymentpage-text').text
    date = html_doc.find('div', 'paymentpage-datetime').find('div', 'date').text.split()

    if date[1] not in dayName:
        data["details"]["date"] = date[3] + "-" + month[date[1]] + "-{:02d}".format(int(date[2].replace(",", "")))
    else:
        recordedWeekday = dayName[date[1]]
        now = datetime.datetime.today()
        nowWeekday = now.weekday()
        if recordedWeekday > nowWeekday:
            diff = nowWeekday + (7-recordedWeekday)
        else:
            diff = nowWeekday - recordedWeekday
        occurance = now - datetime.timedelta(days=diff)

        data["details"]["date"] = str(occurance.year) + "-{:02d}".format(occurance.month) + "-{:02d}".format(occurance.day)


    return data


# Parse the Facebook ID
def GetFbId(passed_user):
    if "facebook" in passed_user:
        fb_id = passed_user.split("/")[4]
    else:
        fb_id = "N/A"
    return fb_id


# Brute Forcing Module
def brute_forcer(name):
    test_case = []
    test_case.append(name.replace(" ", "-"))
    test_case.append(name.replace(" ", ''))
    test_case.append(name.split(" ")[1] + "-" + name.split(" ")[0])
    test_case.append(name.split(" ")[1] + name.split(" ")[0])
    test_case.append(name.replace(" ", "-") + "1")
    test_case.append(name.replace(" ", "-") + "-1")
    test_case.append(name.replace(" ", "-") + "-2")
    test_case.append(name.replace(" ", "-") + "-3")
    test_case.append(name.replace(" ", "-") + "-4")
    test_case.append(name.replace(" ", "-") + "-5")
    test_case.append(name.replace(" ", "-") + "-6")
    test_case.append(name.replace(" ", "-") + "-7")

    for j in range(0, 12):
        url = 'https://api.venmo.com/v1/users/{}'.format(test_case[j])
        print("\n[+] USER DATA: Requesting {}".format(url))
        resp = GetDataFromVenmo(url)
        data = resp.json()
        if 'error' not in data:
            print(
                "[+] User found: {0}\n\t Details: {1},{2},{3}".format(data['data']['display_name'], data['data']['id'],
                                                                      data['data']['friends_count'],
                                                                      data['data']['profile_picture_url']))
            if "venmopics" in data['data']['profile_picture_url'] or "facebook" in data['data']['profile_picture_url']:
                pic = data['data']['profile_picture_url']
                get_profile_pic(pic, test_case[j])
        else:
            print("[-] User not found")
        time.sleep(1)


# The HTTP headers always have content type of jpeg but some are png and I've even found gif. This checks to make sure our file type is right and saves it accordingly
def file_check(f):
    if imghdr.what(f) == "png":
        os.rename(f, str(f.split('.')[0]) + '.png')
    elif imghdr.what(f) == "gif":
        os.rename(f, str(f.split('.')[0]) + '.gif')


# Function for making a request to download the profile picture
def get_profile_pic(pic, file_name):
    request = requests.get(pic, verify=False)
    with open(file_name + '.jpg', 'wb') as f:
        f.write(request.content)
        file_check(file_name + '.jpg')


# Create directory to save work
def create_dir(d):
    if os.path.isdir('./' + d):
        os.chdir(d)
    else:
        os.mkdir(d)
        os.chdir(d)


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

######Main#######
data_format = args.format

# If given a folder name, create a new directory
# if args.dir:
#	create_dir(args.dir)

# Run this if using the "known user" option
if args.user:
    create_dir(args.user)
    user = GetUserData(args.user)
    if args.output:
        with open(args.user + '.csv', 'w') as f:
            # Write User_ID,User_Name,Display_Name,Friends_Count,Join_Date,Profile_Pic_URL
            f.write("User_ID,User_Name,Display_Name,Friends_Count,Join_Date,Profile_Pic_URL\n")
            f.write(
                "{0},{1},{2},{3},{4},{5}\n".format(str(user[6]), str(user[0]), str(user[1]), str(user[4]), str(user[7]),
                                                   str(user[5])))
    # print ("<urn:venmo:id:{0}> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <urn:venmo:venmoRecord> .".format(user[6]))
    #	print ("<urn:venmo:id:{0}> <urn:venmo:hasDisplayName> <urn:venmo:dname:{1}> ".format(user[6],user[1].replace(" ","+")))
    #	print ("<urn:venmo:id:{0}> <urn:venmo:hasUsername> <urn:venmo:uname:{1}> ".format(user[6],user[0]))
    #	print ("<urn:venmo:id:{0}> <urn:venmo:hasJoinDate> \"{1}\"^^<http://www.w3.org/2001/XMLSchema#dateTime> .".format(user[6],user[7]))
    #	if user[8]!="N/A":
    #		print ("<urn:venmo:id:{0}> <urn:venmo:hasFbId> <urn:fb:id:{1}> .".format(user[6],user[8]))\
    # else:
    print("\tDisplay Name: {0}".format(user[1]))
    print("\tFriends Count: {0}".format(user[4]))
    print("\tProfile Picture: {0}".format(user[5]))
    print("\tJoin Date: {0}".format(user[7]))
    data = GetUserTransactions(args.user)
    if args.output:
        with open(args.user + '.csv', 'a') as f:
            # Write User_ID,User_Name,Display_Name,Friends_Count,Join_Date,Profile_Pic_URL
            f.write("Transaction Data\n")
            f.write("Donor_Name,Donor_UserName,Recipient_Name,Recipient_UserName,Transaction__Text,Transaction_Date\n")
            for tr in data["details"]:
                f.write("{0},{1},{2},{3},{4},{5}\n".format(str(tr["donor_name"]), str(tr["donor_username"]),
                                                           str(tr["recipient_name"]), str(tr["recipient_username"]),
                                                           str(tr["text"].encode("utf-8")), str(tr["date"])))

    for k in data["details"]:
        for l in k:
            print("\t" + l + ": " + k[l])
        print("\n")
    for k in data["friends"]:
        print("\t" + k)

# Crawl friends
if args.crawl:
    for friend in data["friends"]:
        friend = friend.replace("/", '')
        user = GetUserData(friend)
        if args.output:
            with open(args.user + '.csv', 'a') as f:
                f.write("{0},{1},{2},{3},{4},{5}\n".format(str(user[6]), str(user[0]), str(user[1]), str(user[4]),
                                                           str(user[7]), str(user[5])))
        print("\tDisplay Name: {0}".format(user[1]))
        print("\tFriends Count: {0}".format(user[4]))
        print("\tProfile Picture: {0}".format(user[5]))
        print("\tJoin Date: {0}".format(user[7]))
        friends_data = GetUserTransactions(friend)
        if args.output:
            with open(args.user + '.csv', 'a') as f:
                # Write User_ID,User_Name,Display_Name,Friends_Count,Join_Date,Profile_Pic_URL
                f.write("Friend Transaction Details - " + friend + "\n")
                f.write(
                    "Donor_Name,Donor_UserName,Recipient_Name,Recipient_UserName,Transaction__Text,Transaction_Date\n")
                for tr in friends_data['details']:
                    f.write("{0},{1},{2},{3},{4},{5}\n".format(str(tr["donor_name"]),
                                                               str(tr["donor_username"]),
                                                               str(tr["recipient_name"]),
                                                               str(tr["recipient_username"]),
                                                               str(tr["text"].encode("utf-8")), str(tr["date"])))

        for k in friends_data["details"]:
            for l in k:
                print("\t" + l + ": " + k[l])
            print("\n")
        for k in friends_data["friends"]:
            print("\t" + k)

# Run this for a single user to brute force
if args.bruteForceUser:
    brute = brute_forcer(args.bruteForceUser)
    print("[+] All done with brute-force, checking file types for picture errors...")
    # Run a check in the current directory for the wonky file types
    for dirfile in os.listdir("./"):
        if dirfile.endswith(".jpg"):
            file_check(dirfile)
    print("[+] Good to go, happy hunting...")

# Run this for brute forcing a list of usernames
if args.bruteForceFile:
    iFile = open(args.bruteForceFile, 'r')
    for i in iFile:
        entry = i.replace("\n", '').replace("\r", '')
        brute = brute_forcer(entry)
    iFile.close()
    for dirfile in os.listdir("./"):
        if dirfile.endswith(".jpg"):
            file_check(dirfile)


