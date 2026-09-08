# 50 High-Priority Database MCQs for HirePro Assessment Preparation

**Q1. What is the primary difference between a database and a Database Management System (DBMS)?**
A) A database is software; a DBMS is hardware.
B) A database is a collection of structured data, while a DBMS is the software used to create, manage, and interact with that data.
C) A DBMS only stores data, while a database provides an interface for users.
D) There is no difference; the terms are synonymous.
**Answer:** B
**Explanation:** A database is the actual organized collection of data. A DBMS (like MySQL or Oracle) is the software layer that allows users and applications to efficiently manage, insert, update, and query that data.

**Q2. In the context of database transactions, what does the "A" in ACID stand for, and what does it ensure?**
A) Accuracy; ensures all data is correct.
B) Atomicity; ensures a transaction is executed completely or not at all.
C) Availability; ensures the database is always online.
D) Aggregation; ensures data can be grouped effectively.
**Answer:** B
**Explanation:** Atomicity means that a transaction is treated as a single, indivisible unit. If any part of the transaction fails, the entire transaction is rolled back, leaving the database unchanged.

**Q3. Which ACID property ensures that once a transaction is committed, the changes are permanently stored even in the event of a system failure?**
A) Atomicity
B) Consistency
C) Isolation
D) Durability
**Answer:** D
**Explanation:** Durability guarantees that committed transactions survive permanent system crashes, typically by writing the changes to non-volatile storage.

**Q4. What is the primary purpose of a Foreign Key in a relational database?**
A) To uniquely identify each record in a single table.
B) To encrypt sensitive data columns.
C) To link one table to another by referencing its primary key, ensuring referential integrity.
D) To speed up data retrieval operations.
**Answer:** C
**Explanation:** A foreign key establishes a relationship between two tables, preventing invalid data from being inserted into the foreign key column because it must be a value contained in the referenced primary key. 

**Q5. How does a Primary Key differ from a Unique Key?**
A) A Primary Key can contain NULL values, but a Unique Key cannot.
B) A Primary Key uniquely identifies a record and cannot contain NULL values, whereas a Unique Key can typically contain one or more NULL values depending on the DBMS.
C) A table can have multiple Primary Keys but only one Unique Key.
D) They are completely identical in function and constraints.
**Answer:** B
**Explanation:** While both enforce uniqueness, a Primary Key is the main identifier for a row and strictly forbids NULLs. A Unique Key allows NULLs (usually restricted to one NULL per column).

**Q6. What is the process of organizing data in a database to reduce redundancy and improve data integrity called?**
A) Denormalization
B) Indexing
C) Normalization
D) Sharding
**Answer:** C
**Explanation:** Normalization divides larger tables into smaller, related tables to eliminate duplicate data and ensure data consistency (e.g., 1NF, 2NF, 3NF).

**Q7. Which SQL command is used to change the structure of an existing table, such as adding or dropping a column?**
A) UPDATE
B) MODIFY
C) ALTER
D) CHANGE
**Answer:** C
**Explanation:** The ALTER command (part of DDL) is used to modify the structure of database objects, including adding, deleting, or altering columns in a table.

**Q8. Which category of SQL commands includes SELECT, INSERT, UPDATE, and DELETE?**
A) DDL (Data Definition Language)
B) DML (Data Manipulation Language)
C) DCL (Data Control Language)
D) TCL (Transaction Control Language)
**Answer:** B
**Explanation:** DML commands are used to manage and manipulate the actual data stored within the database tables.

**Q9. What does the TCL command `ROLLBACK` do?**
A) Restores the database from a backup file.
B) Undoes transactions that have not yet been saved to the database.
C) Permanently saves all open transactions.
D) Deletes all data from a table while keeping its structure.
**Answer:** B
**Explanation:** `ROLLBACK` reverts the database to the last committed state, undoing any uncommitted changes made by the current transaction.

**Q10. What is the difference between the `CHAR` and `VARCHAR2` (or `VARCHAR`) data types?**
A) CHAR stores numbers; VARCHAR stores text.
B) CHAR stores variable-length data; VARCHAR stores fixed-length data.
C) CHAR stores fixed-length character data and pads unused space, while VARCHAR stores variable-length data and does not pad unused space.
D) There is no difference; they are aliases for the same type.
**Answer:** C
**Explanation:** `CHAR` allocates fixed memory and pads shorter strings with spaces. `VARCHAR` only uses as much space as the string requires, saving storage.

**Q11. Which SQL clause is used to filter the results of an aggregate function?**
A) WHERE
B) HAVING
C) FILTER
D) GROUP BY
**Answer:** B
**Explanation:** The `WHERE` clause filters individual rows before aggregation, whereas the `HAVING` clause filters grouped records after aggregate functions have been applied.

**Q12. What will the `COUNT(*)` function return?**
A) The number of distinct values in a specific column.
B) The total number of rows in a table, including rows with NULL values.
C) The sum of all numeric values in a column.
D) The number of non-NULL values in a specific column.
**Answer:** B
**Explanation:** `COUNT(*)` counts every row in the result set, regardless of whether any columns contain NULL values. 

**Q13. In SQL, what is a subquery?**
A) A secondary database connection.
B) A query placed inside another query, such as within a SELECT, FROM, or WHERE clause.
C) A query that updates the database schema.
D) A query that fails to execute.
**Answer:** B
**Explanation:** A subquery (or inner query) is nested inside a larger query (outer query). The inner query executes first, passing its results to the outer query.

**Q14. Which type of JOIN returns every row from the first table combined with every row from the second table?**
A) INNER JOIN
B) LEFT JOIN
C) CROSS JOIN
D) FULL OUTER JOIN
**Answer:** C
**Explanation:** A CROSS JOIN produces a Cartesian product, meaning it does not require a join condition and combines every row of table A with every row of table B.

**Q15. How does an INNER JOIN behave?**
A) It returns all rows from the left table and matched rows from the right table.
B) It returns only the rows that satisfy the join condition (matches in both tables).
C) It returns all rows from both tables, filling in NULLs where there is no match.
D) It joins a table to itself.
**Answer:** B
**Explanation:** INNER JOIN requires a join condition (using `ON`) and only retrieves rows where there is a match in both the left and right tables.

**Q16. What is the primary difference between `RANK()` and `DENSE_RANK()` window functions?**
A) `RANK()` skips the next rank number after duplicate values, while `DENSE_RANK()` does not leave gaps in numbering.
B) `DENSE_RANK()` skips the next rank number after duplicate values.
C) `RANK()` cannot be used with the `PARTITION BY` clause.
D) There is no difference; they produce the identical outputs.
**Answer:** A
**Explanation:** If two rows share rank 1, `RANK()` assigns the next row rank 3. `DENSE_RANK()` assigns the next row rank 2, ensuring no gaps.

**Q17. Which function retrieves the value from the previous row in the same result set without using a self-join?**
A) LEAD()
B) PREVIOUS()
C) LAG()
D) ROW_NUMBER()
**Answer:** C
**Explanation:** `LAG()` accesses data from a preceding row in the same result set, making it highly useful for comparing consecutive rows and calculating differences.

**Q18. What is a View in a database?**
A) A physical copy of a table optimized for reading.
B) A virtual table based on the result-set of an SQL statement.
C) An index that speeds up `SELECT` queries.
D) A graphical interface for database management.
**Answer:** B
**Explanation:** A standard View does not store data itself; it is a saved query that acts as a virtual table, pulling live data from underlying tables when queried.

**Q19. How does a Materialized View differ from a standard View?**
A) A Materialized View is only stored in RAM.
B) A Materialized View is a physical table that stores the precomputed results of a query, requiring periodic refreshes to stay updated.
C) A Materialized View can only pull data from one table.
D) A Materialized View automatically writes changes back to the source tables.
**Answer:** B
**Explanation:** Because it stores data physically on disk, reads from a Materialized View are much faster, but the data may be stale if not refreshed regularly.

**Q20. What is an Index in SQL?**
A) A constraint that prevents duplicate data entry.
B) A physical database object that helps in the faster searching and retrieval of data.
C) A temporary table used for complex joins.
D) A backup file of the database.
**Answer:** B
**Explanation:** Indexes act like a book's index; they allow the database engine to find rows quickly without having to scan the entire table.

**Q21. What is a defining characteristic of a Clustered Index?**
A) It creates a separate structure with pointers to the data rows.
B) It allows multiple clustered indexes per table.
C) It sorts and physically stores the data rows in the table based on their key values.
D) It can only be applied to foreign keys.
**Answer:** C
**Explanation:** Because a clustered index dictates the physical storage order of the data on disk, a table can only have one clustered index.

**Q22. What is a significant trade-off of heavily indexing a database table?**
A) It slows down `SELECT` queries.
B) It removes all foreign key constraints.
C) It creates additional overhead for write operations (INSERT, UPDATE, DELETE) because the index structures must also be updated.
D) It prevents the use of aggregate functions.
**Answer:** C
**Explanation:** While indexes vastly speed up read operations, they consume storage space and slow down write operations because the database must maintain the index.

**Q23. Which SQL operator is used to filter records based on a specified pattern?**
A) IN
B) BETWEEN
C) LIKE
D) MATCH
**Answer:** C
**Explanation:** The `LIKE` operator is used in a `WHERE` clause to search for a specified pattern in a column, often utilizing wildcards like `%` and `_`.

**Q24. How do you prevent a deadlock in a database?**
A) By disabling all indexes.
B) By ensuring all transactions acquire locks on resources in the same predictable order.
C) By dropping foreign key constraints.
D) By increasing the RAM of the database server.
**Answer:** B
**Explanation:** Deadlocks occur when two transactions indefinitely wait for each other to release locks. Enforcing a consistent lock-acquisition order prevents circular waiting.

**Q25. What is an SQL Cursor?**
A) A pointer used to fetch and process rows one by one from a result set.
B) A function that automatically updates timestamps.
C) A visual indicator in a database GUI.
D) A backup mechanism for uncommitted data.
**Answer:** A
**Explanation:** When a query returns multiple rows, a cursor allows a procedural language (like PL/SQL or T-SQL) to iterate through the result set row by row for complex logic.

**Q26. Which type of cursor reflects all changes (inserts, updates, deletes) made to the data while the cursor is open?**
A) STATIC
B) DYNAMIC
C) FORWARD_ONLY
D) KEYSET
**Answer:** B
**Explanation:** A DYNAMIC cursor constantly updates its result set as the underlying data changes, unlike a STATIC cursor which acts as a static snapshot.

**Q27. What is the fundamental difference between relational (SQL) databases and NoSQL databases?**
A) SQL databases do not support transactions, while NoSQL databases do.
B) SQL databases use structured tables with fixed schemas, whereas NoSQL databases use flexible, schema-less structures like key-value pairs or documents.
C) SQL databases are only for local storage, while NoSQL is for the cloud.
D) NoSQL databases require strict normal forms.
**Answer:** B
**Explanation:** Relational databases demand a predefined schema (tables, rows, columns). NoSQL databases allow for dynamic schemas and varied data models (Document, Graph, Key-Value).

**Q28. What is the purpose of database triggers?**
A) To manually start a database backup.
B) To automatically enforce rules, validations, or execute code before or after data changes (INSERT, UPDATE, DELETE).
C) To generate automatic reports.
D) To optimize slow-running queries.
**Answer:** B
**Explanation:** Triggers are special stored procedures that the database engine automatically fires in response to specific events on a particular table.

**Q29. Which technique protects a web application's database from SQL Injection attacks?**
A) Storing passwords in plain text.
B) Using parameterized queries or prepared statements.
C) Granting full administrative access to the web user.
D) Disabling the `WHERE` clause.
**Answer:** B
**Explanation:** Parameterized queries treat user input strictly as data rather than executable code, completely neutralizing SQL injection attempts.

**Q30. What does the `UNION` operator do?**
A) Joins two tables side-by-side based on a common key.
B) Combines the result sets of two or more `SELECT` statements into a single column structure, removing duplicate rows.
C) Combines result sets but keeps all duplicate rows.
D) Intersects two tables to find common values.
**Answer:** B
**Explanation:** `UNION` stacks the results vertically. It requires the same number of columns with compatible data types. To keep duplicates, you must use `UNION ALL`.

**Q31. Which of the following best describes the "N+1 query problem"?**
A) A bug where the primary key increments by N+1 instead of 1.
B) A performance bottleneck where an ORM executes one query to fetch entities, and then executes an additional query for each entity to fetch its related data.
C) A transaction that fails to commit N times before succeeding on the N+1 attempt.
D) Creating an index on a table that already has N indexes.
**Answer:** B
**Explanation:** This is a common inefficiency in application development. It is resolved by eagerly loading related data using a `JOIN` rather than looping through individual secondary queries.

**Q32. In the context of database concurrency, what is a "Dirty Read"?**
A) Reading a record that has been deleted by a committed transaction.
B) Reading uncommitted data from another transaction that might eventually be rolled back.
C) Reading a table without using an index.
D) Reading corrupted physical data from a disk drive.
**Answer:** B
**Explanation:** A dirty read occurs when isolation levels are too low, allowing Transaction A to see the uncommitted changes made by Transaction B.

**Q33. Which transaction isolation level completely prevents dirty reads, non-repeatable reads, and phantom reads?**
A) Read Uncommitted
B) Read Committed
C) Repeatable Read
D) Serializable
**Answer:** D
**Explanation:** Serializable is the highest isolation level. It guarantees complete isolation by ensuring concurrent transactions execute sequentially, though it severely impacts concurrency and performance.

**Q34. What is a Composite Key?**
A) A primary key that automatically generates random strings.
B) A key that combines multiple columns to uniquely identify a row in a table.
C) A foreign key that references multiple tables.
D) An index used exclusively for string matching.
**Answer:** B
**Explanation:** When a single column cannot guarantee uniqueness, two or more columns can be combined to form a composite primary key.

**Q35. How do you delete all data from a table without logging individual row deletions, leaving the table structure intact?**
A) DELETE FROM table_name;
B) DROP TABLE table_name;
C) TRUNCATE TABLE table_name;
D) ALTER TABLE table_name DROP DATA;
**Answer:** C
**Explanation:** `TRUNCATE` is a DDL command that quickly removes all rows by deallocating the data pages, making it much faster than `DELETE` (which is a DML command that logs every row deletion).

**Q36. What does the `EXISTS` operator do in a SQL query?**
A) Checks if a specific table exists in the database schema.
B) Returns TRUE if a subquery returns one or more records.
C) Verifies if a variable is not NULL.
D) Determines if an index is actively being used.
**Answer:** B
**Explanation:** `EXISTS` is a logical operator used to test for the existence of any record in a subquery, stopping its search as soon as it finds the first match.

**Q37. Which function would you use to find the highest salary in an `Employees` table?**
A) TOP(Salary)
B) CEILING(Salary)
C) MAX(Salary)
D) HIGHEST(Salary)
**Answer:** C
**Explanation:** `MAX()` is an aggregate function that returns the largest value in a specified column.

**Q38. What is the difference between `DELETE` and `DROP`?**
A) `DROP` removes specific rows; `DELETE` removes the entire database.
B) `DELETE` removes records from a table (DML), whereas `DROP` entirely removes the table structure and its data from the database (DDL).
C) Both perform the exact same function.
D) `DELETE` cannot be rolled back, but `DROP` can.
**Answer:** B
**Explanation:** `DELETE` is used for manipulating data within a structure and can be rolled back. `DROP` destroys the entire schema object completely.

**Q39. What is a "Self Join"?**
A) When a table joins with a completely different database.
B) A query where a table is joined with itself, often used to query hierarchical data.
C) An automatic join performed by the database engine without an `ON` clause.
D) A join that relies solely on primary keys.
**Answer:** B
**Explanation:** A self-join treats a single table as if it were two separate tables by using table aliases, useful for scenarios like finding employees and their managers within the same `Employee` table.

**Q40. What is an Entity-Relationship (ER) diagram?**
A) A flowchart for backend application logic.
B) A visual representation of the database schema, showing entities (tables), attributes (columns), and the relationships between them.
C) A tool for monitoring database CPU usage.
D) A strict NoSQL data model format.
**Answer:** B
**Explanation:** ER diagrams are essential during the design phase of a database to map out how different data objects interact and relate to one another.

**Q41. In the context of database scaling, what does "Sharding" mean?**
A) Replicating the entire database across multiple servers for redundancy.
B) Horizontal partitioning of a database, splitting a large table into smaller, faster, more easily managed pieces distributed across multiple servers.
C) Upgrading the RAM and CPU of a single database server.
D) Encrypting database backups.
**Answer:** B
**Explanation:** Sharding distributes the data load across multiple machines based on a shard key, enabling massive horizontal scalability.

**Q42. Which of the following is true regarding `NULL` values in SQL?**
A) `NULL` is equivalent to an empty string `""`.
B) `NULL` is equivalent to the number `0`.
C) `NULL` represents a missing or unknown value and cannot be compared using standard operators like `=` or `<>`.
D) `NULL` values cannot be stored in a Foreign Key column.
**Answer:** C
**Explanation:** Because `NULL` is unknown, `NULL = NULL` evaluates to unknown. You must use `IS NULL` or `IS NOT NULL` to check for it.

**Q43. What is the main advantage of Stored Procedures?**
A) They completely eliminate the need for indexes.
B) They allow for NoSQL syntax within a relational database.
C) They group SQL statements into a compiled, reusable unit stored on the server, reducing network traffic and improving execution speed.
D) They automatically back up the database upon execution.
**Answer:** C
**Explanation:** Stored procedures pre-compile execution plans, making complex logic faster and more secure since the application only needs to send the procedure call rather than massive query strings.

**Q44. What does the `COALESCE` function do?**
A) Merges two tables together.
B) Returns the first non-NULL value in a list of expressions.
C) Converts a string to an integer.
D) Calculates the average of a grouped dataset.
**Answer:** B
**Explanation:** `COALESCE(val1, val2, val3)` evaluates the arguments in order and returns the first one that is not `NULL`.

**Q45. What is a "Candidate Key"?**
A) A key currently being considered for deletion.
B) Any column or set of columns that can uniquely identify a record and could potentially be chosen as the Primary Key.
C) A key specifically designed for indexing.
D) A foreign key that references a unique index.
**Answer:** B
**Explanation:** A table may have multiple attributes that ensure uniqueness (e.g., Email, SSN, Employee_ID). Each of these is a Candidate Key, and the database designer selects one to be the Primary Key.

**Q46. Which SQL operator is used to give a temporary, readable name to a column or table during a query?**
A) ALIAS
B) NAME
C) RENAME
D) AS
**Answer:** D
**Explanation:** The `AS` keyword creates an alias (e.g., `SELECT Employee_ID AS ID FROM Employees`), which makes the output or the query itself easier to read.

**Q47. If you need to retrieve all unique, non-duplicate values from a specific column, which keyword must follow the `SELECT` statement?**
A) UNIQUE
B) DISTINCT
C) SPECIFIC
D) SINGLE
**Answer:** B
**Explanation:** `SELECT DISTINCT column_name` filters the result set to return only differing values, eliminating any duplicates.

**Q48. In database architecture, what does OLAP stand for?**
A) Online Application Processing
B) Online Analytical Processing
C) Offline Analytical Processing
D) Object-Level Application Protocol
**Answer:** B
**Explanation:** OLAP systems are optimized for complex data analysis, reporting, and data warehousing, contrasting with OLTP (Online Transaction Processing) systems which handle high volumes of fast, everyday transactions.

**Q49. Which of the following joins is considered an "Outer Join"?**
A) CROSS JOIN
B) FULL JOIN
C) EQUI JOIN
D) SELF JOIN
**Answer:** B
**Explanation:** Outer joins include LEFT OUTER, RIGHT OUTER, and FULL OUTER joins. They return matched rows plus unmatched rows from one or both tables, filling missing sides with NULLs.

**Q50. What does the `GROUP BY` clause do?**
A) It sorts the result set in ascending order.
B) It aggregates identical data into single rows, usually used in conjunction with aggregate functions like COUNT, MAX, or SUM.
C) It joins multiple tables based on identical foreign keys.
D) It partitions a table physically on the disk.
**Answer:** B
**Explanation:** `GROUP BY` arranges data with the same values into summary rows, enabling you to calculate metrics (like total sales) for specific groups (like per department).
