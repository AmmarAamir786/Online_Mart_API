FROM python:3.12
#It tells Docker to use the official Python 3.12 image as the foundation for your custom image. 

COPY . /app/
#This command copies all the files and directories from your current working directory (.) 
#and pastes into the directory /app/ within the container. 

WORKDIR /app
#This line sets the working directory inside the container to /app/. 
#Since your application code is copied to /app/, this ensures that the following commands operate on the correct files.

RUN pip install poetry
#Installs poetry inside your container

RUN poetry config virtualenvs.create false
#This command tells Poetry not to create a virtual environment within the container. 
#You don't necessarily need a separate virtual environment because the container itself acts as a self-contained environment.

RUN poetry install --no-root --no-cache --no-interaction
#This command installs all the dependencies listed in your pyproject.toml file into your container.
    #--no-root: Installs packages without requiring root privileges.
    #--no-cache: Skips using the local cache and downloads fresh packages. Useful for the first build or debugging purposes.
    #--no-interaction: Performs the installation without prompting for user input.

CMD ["poetry", "run", "uvicorn", "product_service.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
#This line defines the default command that will be executed when you run your Docker container