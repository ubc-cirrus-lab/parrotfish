This README from https://github.com/kmu-bigdata/serverless-faas-workbench/wiki/iperf3
## Network - iperf3

**Library** : subprocess

**EC2 Setting**
1. Start your EC2 instance, Configure EC2 Network and Subnet(same Lambda functions)
![image](https://user-images.githubusercontent.com/10591350/56786966-d48bd500-6835-11e9-9e34-695d65569854.png)
2. Configure your Security Group
![image](https://user-images.githubusercontent.com/10591350/56786950-c76ee600-6835-11e9-96bd-6a459a7f50b1.png)
3. Check your EC2 internal-ip (ex : 172.31.XX.XX)
4. Install iperf3
```bash
sudo yum -y install iperf3
```
5. Start iperf3 server
default port : 5201
```bash
sudo iperf3 -s -p [PORT]
```
6. Check your Lambda VPC Permission
AWSLambdaVPCAccessExecutionRole
![image](https://user-images.githubusercontent.com/10591350/56787002-fb4a0b80-6835-11e9-8d9a-a848a75769f6.png)

7. Config your Lambda Network
![image](https://user-images.githubusercontent.com/10591350/56787081-4ebc5980-6836-11e9-86b0-7c6d724116eb.png)


**Lambda payload**(test-event) example:

[iperf3 doc](https://iperf.fr/iperf-doc.php)

server_ip : EC2 internal ip 

server_port : iperf3 server port

reverse options : True or False
 - We can let a client(Lambda) work as either a data uploader(default / False) or downloader(with -R options / True).
 - True : downloader
 - False : uploader

test_time : Sets the interval time in seconds between periodic bandwidth, jitter, and loss reports. 

```json
{
    "server_ip": [SERVER_IP],
    "server_port": [SERVER_PORT],
    "test_time": [NUMBER_OF_TEST_TIME],
    "reverse" : [REVERSE_OPTION] 
```

**Lambda Output** : network sender and recevier bandwidth