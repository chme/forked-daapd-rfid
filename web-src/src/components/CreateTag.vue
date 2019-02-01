<template>
  <div class="modal is-active">
    <div class="modal-background" v-on:click="$emit('close')"></div>
    <div class="modal-content">
      <div class="box" v-if="step === 'select'">
        <p class="title is-5">Select album</p>
          <div class="field">
            <p class="control is-expanded has-icons-left">
              <input class="input is-rounded is-shadowless" type="text" placeholder="Search" v-model="search_query" ref="search_field">
              <span class="icon is-left">
                <i class="mdi mdi-magnify"></i>
              </span>
            </p>
          </div>
        <hr>
        <article class="media" v-for="album in filtered_list" :key="album.id" v-if="search_query === '' || album.name.indexOf(search_query) >= 0 || album.artist.indexOf(search_query)">
          <div class="media-content">
            <div class="media-content">
              <p class="title is-6">{{ album.name }}</p>
              <p class="subtitle is-6">{{ album.artist }}</p>
            </div>
          </div>
          <div class="media-right">
            <button class="button is-link" v-on:click="createTag(album.uri)"><span class="icon"><i class="mdi mdi-arrow-right"></i></span></button>
          </div>
        </article>
      </div>
      <article v-if="step === 'write'" class="message is-warning">
        <div class="message-body">
          <p>{{ message.text }}</p>
        </div>
      </article>
    </div>
    <button class="modal-close is-large" aria-label="close" v-on:click="$emit('close')"></button>
  </div>
</template>

<script>
import axios from 'axios'
import webapi from '@/forked-daapd-api'

export default {
  name: 'CreateTag',
  data: function () {
    return {
      step: 'select',
      search_query: '',
      albums: { items: [], total: 0 }
    }
  },

  created: function () {
    webapi.load_albums().then(({ data }) => {
      this.albums = data
    })
  },

  computed: {
    message () {
      return this.$store.state.message
    },

    filtered_list () {
      if (!this.search_query) {
        return this.albums.items
      }
      return this.albums.items.filter(album => {
        return album.name.toLowerCase().includes(this.search_query.toLowerCase())
                || album.artist.toLowerCase().includes(this.search_query.toLowerCase())
      })
    }
  },

  methods: {
    createTag: function (content) {
      this.$store.commit('setMessage', { 'id': 'WRITE_TAG', 'text': 'Hold a Classic 1K MIFARE tag against the NFC reader Module (MFRC522) to create a new tag.' })
      this.step = 'write'
      axios.post('/api/tags/create', { 'content': content }).then(() => {
        // console.log(data)
      })
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
