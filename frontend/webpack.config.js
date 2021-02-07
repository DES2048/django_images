const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const BundleTracker = require('webpack-bundle-tracker');
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin
const {CleanWebpackPlugin} = require('clean-webpack-plugin')

const outputPath = path.resolve(__dirname, 'dist');

module.exports = {
  entry: './src/main.js',
  output: {
    filename: '[name].[contenthash].js',
    path: outputPath,
  },
  optimization: {
    splitChunks: {
      chunks: 'all',
    }
  },
  module: {
    rules: [
        {
            test: /\.css$/,
            use: [
              {
                  loader: MiniCssExtractPlugin.loader,
                  options: {}
              },
              'css-loader',
            ],
        },
    ],
 },
 plugins: [
     new MiniCssExtractPlugin({
         filename: '[name].[contenthash].css'
     }),
     new BundleTracker({
         filename: path.resolve(outputPath, 'webpack-stats.json')
     }),
     new CleanWebpackPlugin()
 ]
};