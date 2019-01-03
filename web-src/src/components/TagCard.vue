<template>
  <div class="card">
    <div class="card-content">
      <div class="media">
        <div class="media-content">
          <p class="title is-5">Unknown content</p>
        </div>
      </div>
      <div class="content">
        Content: {{ tag.content }}<br>
        Tag-ID: {{ tag.id }}<br>
        <time datetime="2016-1-1">11:09 PM - 1 Jan 2016</time>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TagCard',
  props: [ 'tag' ],
  data: function () {
    return {
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
