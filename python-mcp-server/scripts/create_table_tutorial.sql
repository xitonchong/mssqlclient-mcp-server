-- Step 1: Create a new database
CREATE DATABASE TestDB;
GO

-- Step 2: Use the new database
USE TestDB;
GO

-- Step 3: Create a simple table for storing employee information
CREATE TABLE Employees (
    EmployeeID INT PRIMARY KEY IDENTITY(1,1),  -- Auto-incrementing ID
    FirstName NVARCHAR(50) NOT NULL,            -- First name (required)
    LastName NVARCHAR(50) NOT NULL,             -- Last name (required)
    Email NVARCHAR(100) UNIQUE,                 -- Email (must be unique)
    Department NVARCHAR(50),                     -- Department (optional)
    Salary DECIMAL(10, 2),                       -- Salary with 2 decimal places
    HireDate DATE DEFAULT GETDATE(),             -- Hire date (defaults to today)
    IsActive BIT DEFAULT 1                       -- Active status (defaults to true)
);
GO

-- Step 4: Insert some sample data
INSERT INTO Employees (FirstName, LastName, Email, Department, Salary)
VALUES 
    ('John', 'Doe', 'john.doe@example.com', 'IT', 75000.00),
    ('Jane', 'Smith', 'jane.smith@example.com', 'HR', 65000.00),
    ('Bob', 'Johnson', 'bob.johnson@example.com', 'Finance', 70000.00);
GO

-- Step 5: Query the data
SELECT * FROM Employees;
GO
