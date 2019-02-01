module.exports = {
  // Runtime compiler is required to compile vue templates
  runtimeCompiler: true,

  // Output path for the generated static assets (js/css)
  outputDir: '../htdocs',

  // Output path for the generated index.html
  indexPath: 'index.html',

  assetsDir: 'static',

  // Do not add hashes to the generated js/css filenames, would otherwise
  // require to adjust the Makefile in htdocs each time the web interface is
  // build
  filenameHashing: false,

  devServer: {
    // Proxy API calls to the server running on localhost:9090
    proxy: {
      '/': {
        target: 'http://musicbox:9090'
      }
    }
  }
}
