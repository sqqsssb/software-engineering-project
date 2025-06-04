'''
Displays a list of products.
'''
<template>
  <div>
    <h1>Products</h1>
    <div v-for="product in products" :key="product._id">
      <h2>{{ product.name }}</h2>
      <p>{{ product.description }}</p>
      <p>${{ product.price }}</p>
      <button @click="addToCart(product)">Add to Cart</button>
    </div>
  </div>
</template>
<script>
import axios from 'axios';
export default {
  data() {
    return {
      products: []
    };
  },
  methods: {
    async fetchProducts() {
      const response = await axios.get('/api/products');
      this.products = response.data;
    },
    addToCart(product) {
      this.$emit('add-to-cart', product); // Emit an event to add the product to the cart
    }
  },
  mounted() {
    this.fetchProducts();
  }
}
</script>
<style>
/* Add your styles here */
</style>