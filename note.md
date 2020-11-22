to minimise docker image:
  - docker compose of: tfserving (engine for captcha breaker), selenium-webserver, and python-fastapi (interface)
  - re-write:
    - catpcha: completely remove tensorflow library from preprocess step 
    - webdriver: rewrite how webdrive communicate with solver and also to its main engine (FAILED - seleniumwire doesn't support remote webdrive. Packaged the browser in main script)
    - python: to serve the result. Also, consider splitting the response so that scraping doesn't hang the whole program

rewrite entire model for end-to-end prediction

docker run -d -p 4444:4444 --shm-size 2g selenium/standalone-firefox:latest


docker run -p 8501:8501 \
--mount type=bind,source=/mnt/f/huyng/Desktop/Programming/TracuuNNT_Scraper/solver/model/catpcha_solver,target=/models/catpcha_solver -e MODEL_NAME=catpcha_solver tensorflow/serving &


docker run -p 8501:8501 \
  --mount type=bind,\
source=/mnt/f/huyng/Desktop/Programming/TracuuNNT_Scraper/tmp/serving/tensorflow_serving/servables/tensorflow/testdata/saved_model_half_plus_two_cpu,\
target=/models/half_plus_two \
  -e MODEL_NAME=half_plus_two -t tensorflow/serving &
