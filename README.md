# Some Scripts for my personal usage

Feel free to use and adapt on your own Risk: no guarantee of functionality and error-freeness. \
Documentation will be given bit by bit. \
In case of any questions, feel free to [ask me](mailto:admin@hoehr.net)

## List of Scripts

### dynDNS

Script for my Raspberry Pi that runs as an cronjob every 24h to get the current external ip of my Router and set it as an A on my domain hoehr.net on the subdomain pi /
create an credentials.env in the same subfolder with your MAIL and API data to adapt

### statusCheck

Script to check and log the internetspeed. Ideal as cronjob on an Raspberry Pi

### changeJDK

Script to change the default JDK on an windowssystems \
Set the paths of the JDKs as var in the script and set %JAVA_HOME%\bin in Path so setUp

### turnierplan

Simple tournament-planning tool in plain html (with bootstrap) and js for quick calculating a tournament and the winners for each game/round/group etc.

### endnotenrechner

Basic calculator for the finalgrade of Winfo-Studies at the University Paderborn. May also work for other Universities and degrees
