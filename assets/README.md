# Setting up

## Creating the database
First, you need to log into the postgres user. This is the default user for postgres. You can do this by running the following command:
```bash
psql -h localhost -p 5432 -d postgres -U postgres
```

Then, you need to create the **Database** and the **Admin user**. You can do this by running the following command:
```sql
CREATE DATABASE obliviondb;
CREATE USER admin PASSWORD 'admin'; -- Then you will be prompted to enter a password
\c obliviondb -- Change the current database to obliviondb (current user is postgres)
GRANT ALL ON SCHEMA public TO admin; -- grant all privileges to the admin user on this database
exit
```

## Create the tables
Now that you have created the database and the user, you need to run the [createTables.sql](createTables.sql) file. You can do this by running the following command:
```bash
psql -h localhost -p 5432 -d obliviondb -U admin -f createTables.sql # Enter password when prompted
```

## Connect to the database using the admin user
You can connect to the database using the admin user by running the following command:
```bash
psql -h localhost -p 5432 -d obliviondb -U admin # Enter password when prompted
```

## Importing libraries
You just need to run the following command:
```bash
py -m pip install -r requirements.txt # Windows
```
```bash
pip install -r requirements.txt # Linux
```