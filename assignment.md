# Assignment

Your test assignment is a simple image tracking tool that is responsible for downloading and rotating the downloaded images.

Please create a Python project to perform the following:
* Locally download 100 images from several websites up to your preference. You can keep the list of the websites in a text file.
* Each folder should have the same name as the website an image was downloaded from.
* Rotate downloaded images 180 degrees. For this to do, you can utilize the `pillow` Python library.
* Considering each image as a Python object, update their status as “processed” (“not-processed” by default) once they are rotated.

Requirements:
* Your code should be fast, so don’t neglect to use multithreading / multitasking / multiprocessing if appropriate. Please measure how fast your code is.
* Your code should have a simple logging mechanism (instead of “prints”) to write some info / debug messages the console and a local file.
* Choose one of any functions in your code, and introduce a unit-test for it using any framework that you are familiar with (unittest, pytest, etc.).

Bonus points:
* Save / update the image status in a local database.
