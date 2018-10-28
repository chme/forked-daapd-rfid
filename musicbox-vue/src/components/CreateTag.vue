<template>
  <div class="modal is-active">
    <div class="modal-background" v-on:click="$emit('close')"></div>
    <div class="modal-content">
      <div class="box">
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
      search_query: '',
      albums: { items: [], total: 0 }
    }
  },

  methods: {
    search: function () {
      if (this.search_query) {
        var searchParams = {
          'type': 'album',
          'expression': 'artist includes "' + this.search_query + '" or album includes "' + this.search_query + '"'
        }

        axios.get(this.$store.state.conf.server + '/api/search', { params: searchParams }).then(({ data }) => {
          this.albums = data.albums ? data.albums : { items: [], total: 0 }
        })
      }
    },

    createTag: function (content) {
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
