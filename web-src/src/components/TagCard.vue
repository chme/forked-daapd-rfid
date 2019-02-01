<template>
  <div class="card">
    <div class="card-image" v-show="album.id && has_image">
      <figure class="image is-square">
        <img :src="image_url" @load="has_image = true" @error="has_image = false">
      </figure>
    </div>
    <div class="card-content">
      <div class="content is-small">
        <p class="title is-5" v-if="album.id">{{ album.name }}</p>
        <p class="subtitle is-6" v-if="album.id">{{ album.artist }}</p>
        <p class="title is-5" v-if="!album.id && tag.id">Unknown content</p>
        <p>
          Content: {{ tag.content }}<br>
          Tag-ID: {{ tag.id }}
        </p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TagCard',
  props: [ 'tag', 'album' ],
  data: function () {
    return {
      has_image: false
    }
  },

  computed: {
    image_url () {
      if (this.album.artwork_url) {
        return this.$store.state.forked_daapd_url + this.album.artwork_url + '?maxwidth=600&maxheight=600'
      }
      return false
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
