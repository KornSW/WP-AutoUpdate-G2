<?php
/**
 * Plugin Name: Hello World Plugin
 * Description: Minimales Demo-Plugin zum Testen der vollautomatischen GitHub-Update-Nachrüstung.
 * Version: 0.0.0
 * Author: KornSW
 * Requires at least: 6.0
 * Requires PHP: 7.4
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

add_shortcode(
    'hello_world_plugin',
    static function () {
        return '<p><strong>Hello World!</strong></p>';
    }
);

add_action(
    'admin_notices',
    static function () {
        if ( ! current_user_can( 'update_plugins' ) ) {
            return;
        }

        echo '<div class="notice notice-info"><p>Hello World Plugin ist aktiv. Shortcode: <code>[hello_world_plugin]</code></p></div>';
    }
);
