<template>
  <div class="modal is-active">
    <div class="modal-background" v-on:click="$emit('close')"></div>
    <div class="modal-content">
      <div class="box" v-if="step === 'select'">
        <p class="title is-5">Select album</p>
        <form v-on:submit.prevent="search">
          <div class="field">
            <p class="control is-expanded has-icons-left">
              <input class="input is-rounded is-shadowless" type="text" placeholder="Search" v-model="search_query" ref="search_field">
              <span class="icon is-left">
                <i class="mdi mdi-magnify"></i>
              </span>
            </p>
          </div>
        </form>
        <hr>
        <p class="content">Search results</p>
        <article class="media" v-for="album in albums.items" :key="album.id">
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

export default {
  name: 'CreateTag',
  data: function () {
    return {
      step: 'select',
      search_query: '',
      albums: { items: [], total: 0 }
    }
  },

  computed: {
    message () {
      return this.$store.state.message
    }
  },

  methods: {
    search: function () {
      if (this.search_query) {
        var searchParams = {
          'type': 'album',
          'expression': 'artist includes "' + this.search_query + '" or album includes "' + this.search_query + '"'
        }

        var host = this.$store.state.conf.daapd_host === 'localhost' ? window.location.hostname : this.$store.state.conf.daapd_host
        axios.get('http://' + host + ':' + this.$store.state.conf.daapd_port + '/api/search', { params: searchParams }).then(({ data }) => {
          this.albums = data.albums ? data.albums : { items: [], total: 0 }
        })
      }
    },

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
