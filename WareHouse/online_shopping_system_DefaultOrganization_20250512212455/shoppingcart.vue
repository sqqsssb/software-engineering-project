'''
Manages the shopping cart functionality.
'''
<template>
  <div>
    <h1>Shopping Cart</h1>
    <div v-for="item in cartItems" :key="item._id">
      <h2>{{ item.name }}</h2>
      <p>${{ item.price }}</p>
      <button @click="removeFromCart(item)">Remove</button>
    </div>
    <button @click="checkout">Checkout</button>
  </div>
</template>
<script>
export default {
  props: {
    cartItems: {
      type: Array,
      required: true
    }
  },
  methods: {
    removeFromCart(item) {
      this.$emit('remove-from-cart', item); // Emit an event to remove the item from the cart
    },
    checkout() {
      this.$emit('checkout'); // Emit an event to handle checkout
    }
  }
}
</script>
<style>
/* Add your styles here */
</style>