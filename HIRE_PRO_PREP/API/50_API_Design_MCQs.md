# 50 High-Priority API Design MCQs for HirePro Assessment Preparation

### Section 1: REST Fundamentals & HTTP Methods

**Q1. The most basic REST APIs use standard HTTP methods to perform Create, Read, Update, and Delete (CRUD) operations on resources that are represented by URLs. Which HTTP method is strictly idempotent and used to replace an entire resource at a specific URI?**
A) POST
B) PATCH
C) PUT
D) POST and PUT
**Answer:** C
**Explanation:** PUT is used to update an existing resource or create a new resource at a specific URI and is strictly idempotent, meaning multiple identical requests have the same effect as a single request. POST is not idempotent.

**Q2. How should you represent a "do something" operation (e.g., triggering a calculation) in a REST API that doesn't correspond to a typical CRUD operation?**
A) Use a GET method with query parameters.
B) Define a resource with a noun matching the action and use the POST method with the action's input data in the request body.
C) Use a custom HTTP method like EXECUTE.
D) Append the action verb directly to the endpoint URL (e.g., `/users/123/calculate`).
**Answer:** B
**Explanation:** To perform a "do something" operation via a REST API, you can define a resource with a noun that matches the action or the results of the action, and simply execute an action with the POST method including input data in the body.

**Q3. When designing an HTTP response, what are the three major components it must include?**
A) URL, Method, Headers
B) Status line (Status Code), Response Headers, and an optional Body.
C) Metadata, Payload, Cookies
D) URI, Authentication Token, JSON payload
**Answer:** B
**Explanation:** An HTTP response generally includes a status line (with the status code), response headers, and the response body containing the data. 

**Q4. You are designing an API endpoint that updates only the "email" field of a User resource, leaving the rest of the object intact. Which HTTP method is most appropriate?**
A) PUT
B) POST
C) UPDATE
D) PATCH
**Answer:** D
**Explanation:** PATCH is specifically used for partial updates to a resource, whereas PUT requires sending the entire representation of the resource.

**Q5. According to REST constraints, what does "Statelessness" mean?**
A) The client must not store any session data.
B) The server does not store any state about the client session; every request from the client must contain all information necessary to understand and process the request.
C) The API cannot use a database.
D) The API must use JSON web tokens.
**Answer:** B
**Explanation:** A stateless nature makes it easier to test, scale, and maintain, as the server treats each request independently without relying on stored session context.

**Q6. Which common data format is characterized as lightweight, human-readable, and widely used for data interchange in modern REST APIs?**
A) XML
B) YAML
C) JSON
D) Protobuf
**Answer:** C
**Explanation:** JSON (JavaScript Object Notation) is a lightweight and human-readable format widely used for data interchange in APIs. 

**Q7. If an API request requires specific data types for input (e.g., only numbers for an age field), ensuring this at the API level is known as what?**
A) Mocking
B) Schema validation
C) Authentication
D) Rate limiting
**Answer:** B
**Explanation:** Schema validation ensures the incoming API payload matches the defined structural and type requirements (e.g., ensuring an age field only contains integers).

**Q8. When an API client attempts to read a resource that successfully processed but has no content to return in the body, which status code is most appropriate?**
A) 200 OK
B) 201 Created
C) 204 No Content
D) 404 Not Found
**Answer:** C
**Explanation:** 204 No Content signifies that the server successfully processed the request, but is not returning any content (common for DELETE operations or empty PUTs).

**Q9. Which HTTP status code class signifies a client error, meaning the consumer sent a malformed or unauthorized request?**
A) 200s
B) 300s
C) 400s
D) 500s
**Answer:** C
**Explanation:** HTTP status codes are organized into classes: 200s are successful, 300s indicate redirection, 400s signify a consumer or client error, and 500s point to a provider or server error.

**Q10. For a server error (5xx class), what is a key security best practice regarding the error response body?**
A) Include the full stacktrace to help the client debug.
B) Return a 200 OK to hide the error from attackers.
C) Avoid revealing sensitive system details, like OS versions, databases, or stacktraces, while offering clear troubleshooting info.
D) Send the error in XML instead of JSON.
**Answer:** C
**Explanation:** For server errors (5xx), avoid revealing sensitive system details, like OS versions, databases, or stacktraces, while still offering clear information to help troubleshoot.

### Section 2: Advanced Routing & Payload Design

**Q11. You are designing an endpoint to retrieve a list of active users. Which URI design is strictly RESTful?**
A) `GET /getUsers?status=active`
B) `POST /users/active`
C) `GET /users?status=active`
D) `GET /users/activeList`
**Answer:** C
**Explanation:** Good API design uses logical naming conventions (nouns instead of verbs) and utilizes query parameters (`?status=active`) for filtering resources.

**Q12. What is the primary purpose of an API Gateway in a microservices architecture?**
A) To act as the primary database for all microservices.
B) To provide a single entry point for clients, routing requests to the appropriate backend services and handling cross-cutting concerns like auth and rate limiting.
C) To convert all XML responses to JSON.
D) To execute frontend JavaScript code.
**Answer:** B
**Explanation:** An API Gateway sits between the client and backend services, acting as a reverse proxy to route requests, aggregate responses, and enforce policies like authentication.

**Q13. How do you implement index-based pagination for an endpoint returning a large dataset?**
A) Send all data in one response and let the client paginate.
B) Use a `GET` parameter specifying the specific byte range of the database.
C) Separate the data into discrete pages, allowing clients to request them by passing a "page" parameter and "limit" parameter in the URL.
D) Use a WebSocket to stream data continuously.
**Answer:** C
**Explanation:** If clients need to access a specific page, index-based pagination separates data into discrete pages, which clients request by passing the number of the “page” as a parameter.

**Q14. What does HATEOAS (Hypermedia as the Engine of Application State) provide in a REST API?**
A) It encrypts the payload for security.
B) It includes hypermedia links in the response, allowing the client to dynamically navigate the API's state transitions.
C) It automatically converts REST to GraphQL.
D) It enforces rate limiting on hypermedia files.
**Answer:** B
**Explanation:** HATEOAS is a constraint of the REST architecture that allows clients to discover available actions and endpoints dynamically via links provided in the API responses.

**Q15. In an API request, metadata such as the accepted response format, authorization tokens, and client types are typically passed where?**
A) In the URL query string
B) In the request body
C) In the request headers
D) In the URI path
**Answer:** C
**Explanation:** Request headers contain metadata about the request as key-value pairs, which is where tokens, content-type, and accept headers are placed.

**Q16. What is the difference between a synchronous and an asynchronous API?**
A) Synchronous APIs return XML; asynchronous APIs return JSON.
B) Synchronous APIs require the client to wait for a response before proceeding; asynchronous APIs return an immediate acknowledgment and process the task in the background.
C) Synchronous APIs use POST; asynchronous APIs use GET.
D) Synchronous APIs are stateless; asynchronous APIs are stateful.
**Answer:** B
**Explanation:** Synchronous APIs block the client until processing is finished. Asynchronous APIs return an immediate status (like 202 Accepted) and notify the client later (e.g., via webhooks).

**Q17. When versioning a REST API, which of the following is considered a standard best practice to avoid breaking existing clients while allowing incremental improvements?**
A) Changing the data types of existing fields in the current version.
B) Including the version number in the URI (e.g., `/api/v1/users`) or in a custom request header.
C) Forcing clients to update their payload without notice.
D) Only allowing one version of the API to be live at a time.
**Answer:** B
**Explanation:** A well-designed API should maintain backward compatibility. Standard versioning practices include URI path versioning (v1) or header versioning to manage this.

**Q18. If a client attempts to create a resource (POST /users) but the server responds that the resource already exists, what is the most semantically correct HTTP status code?**
A) 400 Bad Request
B) 404 Not Found
C) 409 Conflict
D) 500 Internal Server Error
**Answer:** C
**Explanation:** 409 Conflict indicates that the request could not be processed because of conflict in the current state of the resource (such as a duplicate entry).

**Q19. What is API virtualization/mocking?**
A) Running the API on a virtual machine.
B) Creating a simulated version of an API that returns predefined responses, allowing frontend developers and testers to work before the actual backend is finished.
C) Using Docker to deploy APIs.
D) Obfuscating API endpoints for security.
**Answer:** B
**Explanation:** API mocking involves creating simulated responses, enabling parallel development and allowing testers to simulate scenarios without relying on the live system.

**Q20. Why might an API developer choose GraphQL over REST for a specific application?**
A) GraphQL is automatically more secure than REST.
B) GraphQL eliminates the need for a database.
C) GraphQL allows clients to request exactly the data they need and nothing more, reducing over-fetching and under-fetching.
D) GraphQL relies exclusively on HTTP GET methods.
**Answer:** C
**Explanation:** Unlike REST which returns fixed data structures, GraphQL enables clients to define the exact shape and fields of the data they require in a single query.

### Section 3: API Security & Authentication

**Q21. What is the fundamental difference between authentication and authorization in APIs?**
A) Authentication uses tokens; authorization uses passwords.
B) Authentication verifies the identity of a client; authorization determines if the client has permissions to access a specific resource.
C) They are synonymous terms.
D) Authentication happens on the client; authorization happens on the server.
**Answer:** B
**Explanation:** Authentication is verifying identity (e.g., username/password), while authorization determines if that verified identity has the necessary permissions to perform an action.

**Q22. Which vulnerability involves an attacker exploiting an endpoint by modifying a parameter (like a User ID) in the API request to access another user's data?**
A) Cross-Site Scripting (XSS)
B) Insecure Direct Object Reference (IDOR)
C) SQL Injection
D) Cross-Site Request Forgery (CSRF)
**Answer:** B
**Explanation:** Insecure Direct Object References (IDOR) occur when an API exposes a direct reference to an internal implementation object, allowing attackers to manipulate the reference to access unauthorized data.

**Q23. In the context of API security, what does CORS stand for and what is its purpose?**
A) Cross-Origin Resource Sharing; it allows a server to indicate any origins (domain, scheme, or port) other than its own from which a browser should permit loading resources.
B) Cross-Origin Rest Security; it encrypts REST payloads.
C) Centralized Object Routing System; it handles load balancing.
D) Certificate Of Resource Security; it manages SSL/TLS certificates.
**Answer:** A
**Explanation:** CORS is a browser security feature that restricts cross-origin HTTP requests, and the API must send specific headers to explicitly allow web applications on different origins to access it.

**Q24. What is a JWT (JSON Web Token) primarily used for in modern API design?**
A) Encrypting database columns.
B) Safely transmitting information between parties as a JSON object, most commonly used for stateless authorization.
C) Validating JSON schemas.
D) Compressing large API payloads.
**Answer:** B
**Explanation:** JWTs are signed (and sometimes encrypted) tokens used to securely assert claims about a user statelessly, without needing to query a session database on every request.

**Q25. Which HTTP header is conventionally used to pass a Bearer token (like a JWT) to an API?**
A) `Token: Bearer <token>`
B) `Authorization: Bearer <token>`
C) `Access-Control: <token>`
D) `Auth-Token: <token>`
**Answer:** B
**Explanation:** The standard HTTP header for passing access tokens is `Authorization`, typically using the `Bearer` schema.

**Q26. What does "Rate Limiting" achieve in API design?**
A) It limits the size of the JSON payload a client can send.
B) It controls the amount of incoming requests a client can make to an API within a specific timeframe to prevent abuse and ensure fair usage.
C) It limits the number of database tables the API can query.
D) It speeds up the response time of the API.
**Answer:** B
**Explanation:** Rate limiting restricts the number of API calls to protect the server from Denial of Service (DoS) attacks, brute-forcing, and resource exhaustion.

**Q27. If an API client exceeds the allowed rate limit, which HTTP status code should the API return?**
A) 401 Unauthorized
B) 403 Forbidden
C) 429 Too Many Requests
D) 503 Service Unavailable
**Answer:** C
**Explanation:** 429 Too Many Requests is the standard status code indicating that the user has sent too many requests in a given amount of time.

**Q28. Which of the following is an effective mitigation strategy against SQL Injection in an API?**
A) Using parameterized queries or Prepared Statements in the backend database operations.
B) Encoding the JSON response in base64.
C) Changing the API from HTTP to HTTPS.
D) Using the PUT method instead of POST.
**Answer:** A
**Explanation:** Injection attacks (like SQL injection) are common vulnerabilities. Using parameterized queries ensures that user input is treated as data rather than executable code.

**Q29. What is OAuth 2.0?**
A) A strict data formatting protocol similar to XML.
B) An industry-standard protocol for authorization that allows third-party applications to grant limited access to an HTTP service.
C) A hashing algorithm used for storing passwords in a database.
D) An API Gateway built by Google.
**Answer:** B
**Explanation:** OAuth 2.0 is a delegation protocol used heavily in API design to allow secure, token-based authorization without sharing user credentials.

**Q30. Why is HTTPS mandatory for secure API communication?**
A) It makes the API run faster.
B) It encrypts the data in transit, preventing man-in-the-middle attacks from reading sensitive headers (like Auth tokens) or payloads.
C) It allows the API to bypass rate limits.
D) It automatically validates JSON schemas.
**Answer:** B
**Explanation:** APIs transmit sensitive data (tokens, personal info). HTTPS uses TLS to encrypt this transmission, preventing eavesdropping and tampering.

### Section 4: Performance, Scalability & Reliability

**Q31. An API endpoint retrieves a massive, rarely changing configuration object. What is the most effective way to improve performance and reduce server load?**
A) Use the POST method for retrieval.
B) Implement caching mechanisms (like Redis) and utilize HTTP cache headers (like `Cache-Control` or `ETag`).
C) Return the data in XML.
D) Require the client to open a WebSocket connection.
**Answer:** B
**Explanation:** Better caching reduces server load and improves performance. Headers like ETag allow the client to conditionally fetch data only if it has changed.

**Q32. In the context of API caching, what does the `ETag` header represent?**
A) The error tag describing a failure.
B) An identifier for a specific version of a resource, allowing the client to check if the resource has been modified.
C) The execution time of the API request.
D) The endpoint tag used for load balancing.
**Answer:** B
**Explanation:** An ETag (Entity Tag) is a hash or identifier of the resource's current state. Clients use it in `If-None-Match` headers to avoid downloading data they already have cached.

**Q33. What is the "N+1 Query Problem" often encountered in API backend performance?**
A) Having an API version N and forcing clients to migrate to N+1.
B) A performance bottleneck where an ORM executes one database query to fetch a list of entities, and then executes an additional query for each entity to fetch related data.
C) Adding one additional header to every API request.
D) When an API gateway scales up by one instance automatically.
**Answer:** B
**Explanation:** This is a common bottleneck causing slow API response times. Fetching relations iteratively causes N additional queries rather than using a single optimized `JOIN`.

**Q34. Which pagination strategy is generally more performant for massive, rapidly changing datasets compared to offset/limit (index-based) pagination?**
A) Cursor-based pagination.
B) Returning the entire dataset asynchronously.
C) Page-number based pagination.
D) XML pagination.
**Answer:** A
**Explanation:** While index-based pagination is common, cursor-based pagination uses a pointer (like a unique ID or timestamp) to fetch the next set, avoiding the massive database performance hit of calculating deep offsets.

**Q35. How does a reverse proxy or load balancer improve an API's reliability?**
A) It formats the database tables.
B) It distributes incoming API traffic across multiple backend servers to prevent any single server from being overwhelmed, ensuring high availability.
C) It writes unit tests for the API.
D) It translates REST into GraphQL automatically.
**Answer:** B
**Explanation:** Load balancers prevent API unreliability and cascading failures under heavy load by routing requests evenly across healthy server instances.

**Q36. You are designing a file upload API. To prevent the API server's memory from being exhausted by a 5GB file, how should the backend handle the payload?**
A) Load the entire file into a JSON string.
B) Use streaming to process the file in chunks rather than buffering it entirely in memory.
C) Convert the file to XML before uploading.
D) Require the user to upload the file 1MB at a time using separate POST requests.
**Answer:** B
**Explanation:** Streaming the incoming request directly to a storage service (like AWS S3) prevents the backend application memory from spiking.

**Q37. What is a Webhook?**
A) A hook in a web browser that captures user clicks.
B) A user-defined HTTP callback initiated by an API server to send real-time data to a client when a specific event occurs.
C) A tool used to mock API requests.
D) A database indexing strategy.
**Answer:** B
**Explanation:** Webhooks allow asynchronous, event-driven communication. Instead of the client polling the API constantly, the API pushes data to the client's URL when an event happens.

**Q38. Why might an API designer choose to implement Circuit Breaker patterns in a microservices backend?**
A) To instantly encrypt database connections.
B) To prevent a failure in a downstream service from cascading to other services by failing fast and temporarily halting requests to the failing service.
C) To limit the rate of API calls from a specific IP.
D) To convert HTTP traffic to HTTPS.
**Answer:** B
**Explanation:** Circuit breakers monitor external calls. If a dependent API fails repeatedly, the circuit trips, stopping further calls and returning an immediate error to prevent resource exhaustion across the system.

**Q39. When load testing an API, what does "throughput" measure?**
A) The time it takes for a single request to travel to the server and back.
B) The number of requests the API can successfully process per unit of time (e.g., requests per second).
C) The amount of database rows the API can delete.
D) The number of security vulnerabilities found.
**Answer:** B
**Explanation:** Throughput measures capacity, whereas latency measures the delay of a single request. Both are crucial for identifying performance bottlenecks.

**Q40. What is the role of Content Delivery Networks (CDNs) in API performance?**
A) They replace the backend database.
B) They cache static API responses (like images or public JSON configurations) at edge servers geographically closer to the user, reducing latency.
C) They format XML into JSON.
D) They manage OAuth tokens.
**Answer:** B
**Explanation:** CDNs cache responses at network edges. When a user requests a resource, the CDN delivers it from the closest node, drastically improving response times.

### Section 5: Architecture, Tooling, & Edge Cases

**Q41. You notice your API responds with a `502 Bad Gateway`. What does this indicate about your architecture?**
A) The client submitted an invalid JSON payload.
B) The API Gateway or reverse proxy received an invalid response from an upstream backend server.
C) The client is not authenticated.
D) The database has exceeded its storage limit.
**Answer:** B
**Explanation:** 502 indicates a server acting as a gateway or proxy received an invalid response from the upstream server it accessed while attempting to fulfill the request.

**Q42. Which API architectural style uses a strict, XML-based messaging protocol and relies heavily on WSDL (Web Services Description Language) for its contract?**
A) REST
B) GraphQL
C) SOAP
D) gRPC
**Answer:** C
**Explanation:** SOAP (Simple Object Access Protocol) is an older, strict XML-based protocol, whereas REST is a more flexible architectural style.

**Q43. What is OpenAPI (formerly Swagger)?**
A) A database system for storing API logs.
B) A widely adopted specification for machine-readable interface files for describing, producing, consuming, and visualizing RESTful web services.
C) An open-source API gateway.
D) A tool for load testing APIs.
**Answer:** B
**Explanation:** OpenAPI allows developers to document APIs rigorously (API documentation importance), making endpoints, payloads, and authentication methods explicit and testable.

**Q44. What is the main advantage of gRPC over traditional REST APIs for internal microservice communication?**
A) gRPC uses JSON, making it easier for humans to read.
B) gRPC is stateless, whereas REST is stateful.
C) gRPC uses Protobuf (Protocol Buffers) and HTTP/2, resulting in highly compressed payloads, multiplexing, and significantly lower latency.
D) gRPC does not require authentication.
**Answer:** C
**Explanation:** gRPC is optimized for high-performance RPC (Remote Procedure Call) and is ideal for fast, internal service-to-service communication.

**Q45. When handling a background task via an API (e.g., generating a massive report), which flow is most appropriate?**
A) The API blocks the connection for 5 minutes until the report is ready.
B) Return a 202 Accepted status with a `Location` header pointing to a status-check URL, allowing the client to poll for completion.
C) Return a 404 Not Found until the report exists.
D) Use a GET request to trigger the generation.
**Answer:** B
**Explanation:** For long-running asynchronous tasks, returning 202 Accepted acknowledges the request. The client can use the provided URL to poll the job's status.

**Q46. In an API CI/CD pipeline, what is "Contract Testing"?**
A) Testing if the developers signed their employment contracts.
B) Verifying that the API consumer and the API provider agree on the structure and format of requests and responses (the contract), ensuring independent deployment safely.
C) Testing the API against a live production database.
D) Testing the frontend UI of the application.
**Answer:** B
**Explanation:** Contract testing is vital in microservices architectures to guarantee that changes in an API provider do not break consumer integrations.

**Q47. If an API request to an idempotent endpoint (like PUT) fails due to a network timeout, what is the safest action for the client?**
A) Never retry the request.
B) Safely retry the exact same request, because idempotent operations will not cause unintended duplicate state changes.
C) Change the method to POST and retry.
D) Delete the resource and start over.
**Answer:** B
**Explanation:** Because PUT is idempotent, sending the same request twice (due to a retry) yields the exact same final state as sending it once.

**Q48. Which header indicates the media type of the resource in an HTTP API response?**
A) Accept
B) Authorization
C) Content-Type
D) Cache-Control
**Answer:** C
**Explanation:** The `Content-Type` header tells the client what data format the response body is in (e.g., `application/json`). The `Accept` header is used by the client to tell the server what format it *wants*.

**Q49. How should a REST API handle sorting and filtering of collections?**
A) By creating distinct URIs for every combination (e.g., `/users/sort/asc/filter/active`).
B) By using query string parameters (e.g., `/users?sort=asc&status=active`).
C) By requiring the client to pass filtering commands in the request body of a GET request.
D) By returning all data and forcing the client side to filter it.
**Answer:** B
**Explanation:** Appending query parameters allows for flexible filtering, sorting, and pagination without cluttering the API path routing layer. 

**Q50. When a client performs a successful POST request to create a new user (`/users`), what is the best practice for the API response?**
A) Return `200 OK` with the text "User created".
B) Return `201 Created` with a `Location` header pointing to the new resource's URI (e.g., `/users/123`), and optionally the created JSON object in the body.
C) Return `204 No Content`.
D) Return `301 Moved Permanently`.
**Answer:** B
**Explanation:** `201 Created` is the semantically correct response for resource creation, and providing the `Location` header allows the client to instantly know where to access the newly created entity.
