-- Create a test database
CREATE DATABASE TestMCP;
GO

-- Switch to the new database
USE TestMCP;
GO

-- Create a Customers table
CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY IDENTITY(1,1),
    CompanyName NVARCHAR(100) NOT NULL,
    ContactName NVARCHAR(100),
    Email NVARCHAR(100),
    Phone NVARCHAR(20),
    City NVARCHAR(50),
    Country NVARCHAR(50),
    CreatedDate DATETIME DEFAULT GETDATE()
);
GO

-- Create a Products table
CREATE TABLE Products (
    ProductID INT PRIMARY KEY IDENTITY(1,1),
    ProductName NVARCHAR(100) NOT NULL,
    Category NVARCHAR(50),
    Price DECIMAL(10,2),
    InStock BIT DEFAULT 1,
    LastUpdated DATETIME DEFAULT GETDATE()
);
GO

-- Create an Orders table
CREATE TABLE Orders (
    OrderID INT PRIMARY KEY IDENTITY(1,1),
    CustomerID INT FOREIGN KEY REFERENCES Customers(CustomerID),
    OrderDate DATETIME DEFAULT GETDATE(),
    TotalAmount DECIMAL(10,2),
    Status NVARCHAR(20)
);
GO

-- Insert sample data into Customers
INSERT INTO Customers (CompanyName, ContactName, Email, Phone, City, Country)
VALUES
    ('Acme Corp', 'John Doe', 'john@acme.com', '555-0100', 'Seattle', 'USA'),
    ('Global Tech', 'Jane Smith', 'jane@globaltech.com', '555-0101', 'London', 'UK'),
    ('Pacific Trade', 'Bob Wilson', 'bob@pacific.com', '555-0102', 'Sydney', 'Australia'),
    ('Euro Solutions', 'Maria Garcia', 'maria@euro.com', '555-0103', 'Madrid', 'Spain'),
    ('Asia Imports', 'Li Wang', 'li@asiaimports.com', '555-0104', 'Tokyo', 'Japan');
GO

-- Insert sample data into Products
INSERT INTO Products (ProductName, Category, Price, InStock)
VALUES
    ('Laptop', 'Electronics', 999.99, 1),
    ('Mouse', 'Electronics', 29.99, 1),
    ('Desk Chair', 'Furniture', 249.99, 1),
    ('Monitor', 'Electronics', 399.99, 0),
    ('Keyboard', 'Electronics', 79.99, 1),
    ('Desk Lamp', 'Furniture', 49.99, 1);
GO

-- Insert sample data into Orders
INSERT INTO Orders (CustomerID, TotalAmount, Status)
VALUES
    (1, 1299.98, 'Completed'),
    (2, 449.98, 'Pending'),
    (3, 999.99, 'Completed'),
    (1, 79.99, 'Shipped'),
    (4, 249.99, 'Pending');
GO

-- Create a simple stored procedure for testing
CREATE PROCEDURE GetCustomerOrders
    @CustomerID INT,
    @MinAmount DECIMAL(10,2) = 0
AS
BEGIN
    SELECT
        o.OrderID,
        c.CompanyName,
        c.ContactName,
        o.OrderDate,
        o.TotalAmount,
        o.Status
    FROM Orders o
    INNER JOIN Customers c ON o.CustomerID = c.CustomerID
    WHERE o.CustomerID = @CustomerID
      AND o.TotalAmount >= @MinAmount
    ORDER BY o.OrderDate DESC;
END;
GO

-- Create another stored procedure with output parameter
CREATE PROCEDURE GetCustomerStats
    @CustomerID INT,
    @OrderCount INT OUTPUT,
    @TotalSpent DECIMAL(10,2) OUTPUT
AS
BEGIN
    SELECT
        @OrderCount = COUNT(*),
        @TotalSpent = ISNULL(SUM(TotalAmount), 0)
    FROM Orders
    WHERE CustomerID = @CustomerID;
END;
GO

PRINT 'Test database setup completed successfully!';
