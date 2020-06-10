#!/usr/bin/env python

import time
import requests
import argparse
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver


####################
# Argument Parsing #
####################

parser = argparse.ArgumentParser(description='Arguments for the CAS benchmark script.')
parser._action_groups.pop()

required = parser.add_argument_group('required arguments')
optional = parser.add_argument_group('optional arguments')

required.add_argument('-u', '--username', required=True, help='A username used to sign in with CAS.')
required.add_argument('-p', '--password', required=True, help='A password used to sign in with CAS.')
optional.add_argument('-i', '--iterations', type=int, default=1, help='Number of times the script will be run.')

args = parser.parse_args()


#######################
# Usability Functions #
#######################

def getFormattedTimestamp():
	return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")


#####################
# CAS API Functions #
#####################

def fetchTicketGrantingTicket(username, password):
	print('[%s] Fetching TGT' % getFormattedTimestamp())

	# Record when function started.
	tgt_start = time.time()

	# Perform API call.
	url = "https://den.apu.edu/cas/v1/tickets"
	headers = {'Content-Type': 'application/x-www-form-urlencoded'}
	payload = 'username=%s&password=%s' % (username, password)
	response = requests.request('POST', url, headers=headers, data=payload)

	# Record how long the function took.
	tgt_elapsed = time.time() - tgt_start

	print('[%s] FINISHED: Fetching TGT - %.2f seconds elapsed.' % (getFormattedTimestamp(), tgt_elapsed))

	return response.text.encode('utf8')

def fetchServiceTicket(service_ticket_url):
	print('[%s] Fetching ST' % getFormattedTimestamp())

	# Record when function started.
	st_start = time.time()

	# Perform API call.
	url = service_ticket_url
	headers = {'Content-Type': 'application/x-www-form-urlencoded'}
	payload = 'service=https%3A//home.apu.edu/app/profile/logintoapp'

	response = requests.request('POST', url, headers=headers, data=payload)

	# Record how long the function took.
	st_elapsed = time.time() - st_start

	print('[%s] FINISHED: Fetching ST - %.2f seconds elapsed.' % (getFormattedTimestamp(), st_elapsed))
	
	return response.text.encode('utf8')



######################
# Selenium Functions #
######################

def initializeSeleniumDriver():
	print('[%s] Initializing Selenium' % getFormattedTimestamp())

	# Record when function started.
	init_start = time.time()
	
	options = webdriver.ChromeOptions()
	options.add_argument('--headless')
	options.add_argument('--no-sandbox')	# required when running as root user. 
	driver = webdriver.Chrome(chrome_options=options, service_args=['--log-path=selenium_cas_auth.log'])
	
	# Record how long the function took.
	init_elapsed = time.time() - init_start

	print('[%s] FINISHED: Initializing Selenium - %.2f seconds elapsed.\n' % (getFormattedTimestamp(), init_elapsed))

	return driver

def navigateToURL(driver, url):
	print('[%s] Navigating to %s' % (getFormattedTimestamp(), url))
	
	# Record when function started.
	nav_start = time.time()

	# Perform the page redirect.
	driver.get(url) 

	# Record how long the function took.
	nav_elapsed = time.time() - nav_start

	print('[%s] FINISHED: Navigating to %s - %.2f seconds elapsed.' % (getFormattedTimestamp(), url, nav_elapsed))

	# Validate page load.
	if (driver.title):
		return True
	return False


################
# Main Program #
################

# Initialize selenium and chromedriver.
driver = initializeSeleniumDriver()
	
def main():
	# Fetch TGT from CAS API.
	CAS_TGT_RESPONSE = fetchTicketGrantingTicket(username=args.username, password=args.password)

	# Parse the TGT response using Beautiful Soup.
	soup = BeautifulSoup(CAS_TGT_RESPONSE, 'html.parser')
	form = soup.find(['form'])
	service_ticket_url = form.get('action')

	# Fetch ST from CAS API.
	CAS_ST_RESPONSE = fetchServiceTicket(service_ticket_url)

	# Form a url using the new CAS service ticket.
	home_login_url = 'https://home.apu.edu/app/profile/logintoapp?ticket=%s' % CAS_ST_RESPONSE

	# Redirect to APU Home using the CAS service ticket.
	navigation_successful = navigateToURL(driver, home_login_url)

	# Check if Selenium successfully navigated to the `home_login_url`.
	if (navigation_successful):
		print '[%s] User successfully redirected to APU Home Dashboard.' % getFormattedTimestamp()
	else:
		print '[%s] Navigation failed.' % getFormattedTimestamp()

benchmark_times = []
for i in range(args.iterations):
	print('[%s] Starting iteration #%s' % (getFormattedTimestamp(), (i+1)))

	# Record when the function started.
	main_start_time = time.time()

	main()

	# Record how long the function took in seconds.
	elapsed = time.time() - main_start_time
	benchmark_times.append(elapsed)

	print('[%s] FINISHED: iteration #%s - %.2f seconds elapsed.\n' % (getFormattedTimestamp(), (i+1), elapsed))

avg = sum(benchmark_times) / len(benchmark_times)
print('Average time after %s iterations: %.2f seconds.' % (args.iterations, avg))
