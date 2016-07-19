# couch-potato

Couch Potato is a custom Alexa Skill which provides a voice interface to control a TV or cable box.

There a number of working components to achieve this feat:  
1. Alexa Skill  
2. AWS Lambda function  
3. Flask web application  
4. Linux Infrared Remote Control (LIRC) module  
5. IR transmitted circuit 

Above is the chronological ordering of the components when completing a request. A user asks Alexa to ask couch potato to complete a given request. The Alexa skill sends a JSON blurb to the Lambda function which parses which intent and other relevant information out and then sends the appropriate HTTP request to the Flask web application running on a Raspberry Pi. The web application then performs the specified action by calling out to the Linux Infrared Remote Control module which has been manually configured with a number of remotes. The LIRC module controls the IR transmitter circuit via the GPIO pins to send signals to the TV and cable box.

Example requests:
- "Alexa ask Couch Potato to list remotes" - Lists all of the available remotes
- "Alexa ask Couch Potato to list keys for {Remote}" - Lists all of the mapped keys for a given remote
- "Alexa ask Couch Potato to press key mute" - Presses the mute key
- "Alexa ask Couch Potato to change channel to {Channel}" - Change the channel to a given channel, i.e. HBO or 870
- "Alexa ask Couch Potato to turn on TV" - Turns on the television
- "Alexa ask Couch Potato to turn up the volume 5 times" - Presses the volume down key 5x


