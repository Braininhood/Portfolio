@echo off
echo 🚀 Importing Local Data to MongoDB Atlas
echo =========================================

echo.
echo This script will import your local data to MongoDB Atlas
echo Make sure you have:
echo ✅ Created MongoDB Atlas account
echo ✅ Created a cluster
echo ✅ Set up database user and network access
echo ✅ Installed MongoDB Database Tools

echo.
set /p atlas_uri="Enter your MongoDB Atlas connection string: "

echo.
echo 📊 Importing dealerships data...
mongoimport --uri "%atlas_uri%" --collection dealerships --file server\database\data\dealerships.json --jsonArray

echo.
echo 📝 Importing reviews data...
mongoimport --uri "%atlas_uri%" --collection reviews --file server\database\data\reviews.json --jsonArray

echo.
echo ✅ Data import completed!
echo Your local dealership and review data is now in MongoDB Atlas
echo.
echo 🔧 Next steps:
echo 1. Update render.yaml with your Atlas connection string
echo 2. Replace: mongodb+srv://dealership:YOUR_PASSWORD@cluster.mongodb.net/dealershipsDB
echo 3. Commit and push to GitHub
echo 4. Deploy to Render!

pause 