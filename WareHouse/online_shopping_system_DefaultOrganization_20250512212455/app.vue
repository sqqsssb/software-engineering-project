'''
Main application component for Vue.js.
'''
<template>
  <div id="app">
    <ProductList @add-to-cart="addToCart" />
    <ShoppingCart :cartItems="cartItems" @remove-from-cart="removeFromCart" @checkout="checkout" />
  </div>
</template>
<script>
import ProductList from './components/ProductList.vue';
import ShoppingCart from './components/ShoppingCart.vue';
export default {
  components: {
    ProductList,
    ShoppingCart
  },
  data() {
    return {
      cartItems: []
    };
  },
  methods: {
    addToCart(product) {
      this.cartItems.push(product); // Add product to cart
    },
    removeFromCart(item) {
      this.cartItems = this.cartItems.filter(cartItem => cartItem._id !== item._id); // Remove item from cart
    },
    checkout() {
      alert('Proceeding to checkout'); // Placeholder for actual checkout logic
    }
  }
}
</script>
<style>
/* Add your styles here */
</style>