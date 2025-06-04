```markdown
# Online Shopping System

Welcome to the Online Shopping System! This application allows users to browse products, add them to a shopping cart, and proceed to checkout. It consists of a front-end built with Vue.js and a back-end powered by Express and MongoDB.

## Main Functions

- **Product Management**: Users can view a list of products, including their names, descriptions, prices, and images.
- **Shopping Cart**: Users can add products to their shopping cart, remove items, and proceed to checkout.
- **User Authentication**: Users can register and log in to their accounts securely.
- **API Integration**: The front-end communicates with the back-end through RESTful API endpoints.

## Installation

### Environment Dependencies

To run the Online Shopping System, you need to install the following dependencies. Make sure you have Node.js and MongoDB installed on your machine.

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd online-shopping-system
   ```

2. **Install back-end dependencies**:
   Navigate to the back-end directory and install the required packages:
   ```bash
   cd backend
   npm install
   ```

3. **Install front-end dependencies**:
   Navigate to the front-end directory and install the required packages:
   ```bash
   cd frontend
   npm install
   ```

### Database Setup

1. **Start MongoDB**:
   Make sure your MongoDB server is running. You can start it using the following command:
   ```bash
   mongod
   ```

2. **Database Configuration**:
   The application is configured to connect to a MongoDB database named `shopping`. Ensure that the connection string in `server.js` is correct.

## How to Use

### Starting the Application

1. **Start the back-end server**:
   Navigate to the back-end directory and run:
   ```bash
   cd backend
   node server.js
   ```

2. **Start the front-end application**:
   Open a new terminal window, navigate to the front-end directory, and run:
   ```bash
   cd frontend
   npm run serve
   ```

3. **Access the Application**:
   Open your web browser and go to `http://localhost:8080` to access the Online Shopping System.

### User Registration and Login

- **Register**: Users can create a new account by sending a POST request to `/api/users/register` with their name, email, and password.
- **Login**: Users can log in by sending a POST request to `/api/users/login` with their email and password. A JWT token will be returned upon successful login.

### Browsing Products

Once logged in, users can view the list of products on the main page. Each product displays its name, description, price, and an "Add to Cart" button.

### Shopping Cart

- **Add to Cart**: Click the "Add to Cart" button on a product to add it to your shopping cart.
- **Remove from Cart**: In the shopping cart section, users can remove items by clicking the "Remove" button next to each item.
- **Checkout**: Click the "Checkout" button to proceed with the checkout process (currently a placeholder).

## Conclusion

The Online Shopping System is a robust application that provides a seamless shopping experience. Feel free to explore the codebase and customize it to meet your needs. For any questions or support, please reach out to the development team.

Happy Shopping!
```