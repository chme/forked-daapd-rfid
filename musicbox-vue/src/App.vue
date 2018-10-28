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
    axios.get('/api/conf').then(response => {
      this.$store.commit('setConf', response.data)
    })
    var socket = new ReconnectingWebSocket(
      'ws://' + window.location.hostname + ':' + window.location.port + '/ws',
      null,
      { reconnectInterval: 5000 }
    )

    socket.onopen = function () {
      socket.send(JSON.stringify({ notify: ['update', 'player', 'options', 'outputs', 'volume', 'spotify'] }))
    }
    socket.onclose = function () {
    }
    socket.onerror = function () {
    }
    socket.onmessage = function (response) {
      alert(response.data)
    }
  }
}
</script>

<style>
</style>
