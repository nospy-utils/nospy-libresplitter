"use strict";

const gulp = require('gulp');
const sass = require('gulp-sass')(require('sass'));
const fs = require('fs');
const fileinclude = require('gulp-file-include');

const OUT_DIR = 'output';
const OUT_CSS_DIR = OUT_DIR + '/css';
const OUT_JS_DIR = OUT_DIR + '/js';
const OUT_IMG_DIR = OUT_DIR + '/img';
const OUT_VENDOR_DIR = OUT_DIR + '/vendor';
const OUT_VENDOR_JS_DIR = OUT_VENDOR_DIR + '/js';
const OUT_VENDOR_IMG_DIR = OUT_VENDOR_DIR + '/img';
const OUT_VENDOR_CSS_DIR = OUT_VENDOR_DIR + '/css';

async function clean() {
    await fs.rmSync(OUT_DIR, {recursive: true, force: true});
}

function build_prep() {
    const folders = [
        OUT_DIR,
        OUT_CSS_DIR,
        OUT_JS_DIR,
        OUT_IMG_DIR,
        OUT_VENDOR_DIR,
        OUT_VENDOR_JS_DIR,
        OUT_VENDOR_IMG_DIR,
        OUT_VENDOR_CSS_DIR,
    ];

    folders.forEach(dir => {
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir);
            console.log('folder created:', dir);
        }
    });
}

function css() {
    return gulp.src('./sass/**/*.sass')
        .pipe(sass().on('error', sass.logError))
        .pipe(gulp.dest('./' + OUT_CSS_DIR));
}

function img() {
    return gulp.src('./img/**', {encoding: false})
        .pipe(gulp.dest('./' + OUT_IMG_DIR));
}

function vendor_js() {
    return gulp.src([
        './node_modules/bootstrap/dist/js/bootstrap.bundle.min.js',
        './node_modules/@popperjs/core/dist/umd/popper.min.js'
    ]).pipe(gulp.dest('./' + OUT_VENDOR_JS_DIR));
}

function vendor_fonts() {
    return gulp.src([
        './node_modules/bootstrap-icons/**/*',
        '!./node_modules/bootstrap-icons/package.json',
        '!./node_modules/bootstrap-icons/README.md',
        '!./node_modules/bootstrap-icons/LICENSE',
        '!./node_modules/bootstrap-icons/bootstrap-icons.svg',
    ]).pipe(gulp.dest('./' + OUT_VENDOR_IMG_DIR))
}

function vendor_css() {
    return gulp.src([
        './node_modules/bootstrap/dist/css/bootstrap.min.css',
    ]).pipe(gulp.dest('./' + OUT_VENDOR_CSS_DIR));
}

function html() {
    return gulp.src('./*.html')
        .pipe(fileinclude({
            prefix: '@@',
            basepath: '@file'
        }))
        .pipe(gulp.dest('./' + OUT_DIR));
}

async function build() {
    await clean();
    build_prep();
    vendor_fonts();
    vendor_css();
    vendor_js();
    img();
    css();
    html();
}

async function watch() {
    await build()
    gulp.watch('./sass/**/*.sass', gulp.series(css));
    gulp.watch('./img/**', gulp.series(img));
    gulp.watch('./*.html', gulp.series(html));
}

exports.default = build;
exports.watch = watch;
exports.clean = clean;
