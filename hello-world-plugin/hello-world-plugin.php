<?php
/**
 * Plugin Name: Hello World Plugin
 * Update URI: https://raw.githubusercontent.com/KornSW/WP-AutoUpdate-G2/master/doc/hello-world-plugin.update.json
 * Plugin URI: https://github.com/KornSW/WP-AutoUpdate-G2
 * Description: Minimales Demo-Plugin zum Testen der vollautomatischen GitHub-Update-Nachrüstung.
 * Version: 1.0.1
 * Author: KornSW
 * Requires at least: 6.0
 * Requires PHP: 7.4
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}


/*************** SELF-UPDATE ***************/
define( 'KSWHELLOWORLD495F_SELF_UPDATE_DIAGNOSTICS', false );
require_once __DIR__ . '/self-update.php';
kswhelloworld495f_bootstrap( __FILE__ );
/*******************************************/

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
