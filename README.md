# Hello world with Java :coffee:
ADDED WEBHOOK TESTING COMMIT 

This
  is a simple **"Hello world"** done with **Java** programming language.

## Source code

Creating a Project
You need somewhere for your project to reside. Create a directory somewhere and start a shell in that directory. On your command line, execute the following Maven goal:

mvn archetype:generate -DgroupId=com.mycompany.app -DartifactId=my-app -DarchetypeArtifactId=maven-archetype-quickstart -DarchetypeVersion=1.4 -DinteractiveMode=false
```

Notice that `System.out.println("Hello world!");` shows the string `"Hello world!"` on the screen.

## Compile program

Build the Project
mvn package

The command line will print out various actions, and end with the following:

 ...
[INFO] ------------------------------------------------------------------------
[INFO] BUILD SUCCESS
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.953 s
[INFO] Finished at: 2019-11-24T13:05:10+01:00
[INFO] ------------------------------------------------------------------------

## Excute the program

java -cp target/my-app-1.0-SNAPSHOT.jar com.mycompany.app.App

