listen carefully you mf 

1. ## first you should create the database by idk maybe magasin_outillage or whatever 

2. make sure that you configure your username and database name and the password correctly, you can do that in the python file called 
  ## sensitive_info 

3. make sure to ignore pycache ,dont be a dumb like me 

4. when you done with that run those commandes :

    # flask db init
    this initialize the database

    # flask db migrate -m "Initial migration"
    this line makes it detect the models that you created in the models file
    make sure you have cryptography installed : 
       ## pip3 install cryptography
    # flask db upgrade
    and this line finally creates  the tables