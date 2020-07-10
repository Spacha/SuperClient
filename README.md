# SuperClient

Tremendously over-engineered solution to an assignment of 'Fundamentals of Internet' course.

**NOTE:** This README is targeted for my assignee but you can read it if you feel like it. Also, while this is interesting and all, if ytou don't have a matching pair of server software to communicate with this, you can't do much with this. The server API is described in `doc/assignment/coursework_2020.pdf`. Write your own server software using that doc, will ya?

## Pre-requisites
* Python 3 (won't work on python2 but portable with minor changes, I believe)
* Terminal or console with black background is preferred for the UI.
* Preferred: Console that uses ANSI (best background color would be black).

I developed the program using Mac OSX and tested with Windows. So it should also work on Windows and Linux.

## Usage

First, make sure you're in the folder with `main.py` file. Then run the following command:

`$ python3 main.py <ip address> <port> <options=emp> <ansi=1>`
* `<ip address>` is the IPv4 address of the target server.
* `<port>` is the port for **TCP**.
* `<options>` is an optional argument that defines which features are enabled:
  * `e` = _encryption_, `m` = _multipart_, `p` = _parity_, `n` = _no extra features_
    * For example, to enable just encryption and multipart: `python3 main.py <...> <...> ep`
    * For example, to disable all extra features: `python3 main.py <...> <...> n`
    * If you pass no options, all features are enabled by default.
* `<ansi=1>` Use `0` to disable ANSI formatting in console output. This is necessary if you're using a system that doesn't naturally support them. I used ANSI character encoding to change colos and format text nicely. If you can, I recommend trying ANSI if you can use OSX or Linux, for example. Default is `1` (enabled).
 * For example, all features active but ANSI disabled: `python3 main.py <...> <...> emp 0`
  

## Technical Details

![Diagram](/doc/diagram-1.png?raw=true "Basic structure of SuperClient")

As stated, the program is overdone with classes and all, so I thought to clarify the design approach a little bit. The basic structure is presented in the diagram above. It doesn't follow any official UML/other structure but it is meant to clarify a bit how things relate to each other.

As we can see, `main.py` file first creates the master class, called `Client`. Client then inits `UI` class in order to print formatted text and some ASCII crap to the console. Then, main.py calls the `start()` method of Client, which starts the actual program. Client then creates an instance of `Log` class, which is used to log/print more detailed debug info on the console.

Client creates and controls TCPConnection and UDPConnection classes, which take care of all the details of TCP and UDP, respectively. They provide an abstraction layer for the complicated communication system we've created.

Client uses UI to tell the user about progress of the program. All other classes use Log class if they need to tell something. 


## My thoughts

I hope this does not cause too much trouble for you. I took the exercise as a fun project and did a lot of unnecessary and overly complicated things. I tried to keep it simple but the main idea was: "if this was a big project, how would I structure it so that it'd scale well?". So I got an object-oriented approach with few classes.

I also had the time to make a simple "console UI" that takes care of the... well, UI stuff. It should work on OSX, Windows and Linux but I can't be 100% sure. The program worked well and without any bugs but after all the over-engineering...

There is still a lot of things that I'd like to make cleaner and structure better but maybe some other time.

Also, one of the driving ideas were that **I'm not allowed to use any other external libraries nor pieces of code**, except sockets & struct libraries that were kind of required (and almost impossible to replicate). So, every line of code and comment is hand-crafted by me (with help of some wappusima).

In the end, I had to roll back to using build-in random number generator, though, since my implementation of random only worked on unix systems.
