<template>
  <div id="app">
    <Navbar/>
    <TagList/>
  </div>
</template>

<script>
import Navbar from './components/Navbar.vue'
import TagList from './components/TagList.vue'
import axios from 'axios'
import ReconnectingWebSocket from 'reconnectingwebsocket'

export default {
  name: 'app',
  components: {
    Navbar, TagList
  },
  created: function () {
    axios.get('/api/conf').then(({ data }) => {
      this.$store.commit('setConf', data)
    })
    axios.get('/api/tags/current').then(({ data }) => {
      this.$store.commit('setCurrentTag', data)
    })

    var socket = new ReconnectingWebSocket(
      'ws://' + window.location.hostname + ':' + window.location.port + '/ws',
      null,
      { reconnectInterval: 5000 }
    )
    // socket.debug = true

    const vm = this
    socket.onopen = function () {
      socket.send(JSON.stringify({ notify: ['update', 'player', 'options', 'outputs', 'volume', 'spotify'] }))
    }
    socket.onclose = function () {}
    socket.onerror = function () {}
    socket.onmessage = function (response) {
      var data = JSON.parse(response.data)
      if (data.type === 'current_tag') {
        vm.$store.commit('setCurrentTag', data.current_tag)
      }
    }
  }
}
</script>

<style>
</style>
