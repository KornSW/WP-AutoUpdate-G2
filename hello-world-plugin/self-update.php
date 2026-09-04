<?php
/**
 * KornSW Self Update Loader
 *
 * Diese Datei darf in mehreren Plugins gleichzeitig vorhanden sein.
 * Klasse/Funktion werden nur einmal definiert, aber jedes Plugin bekommt
 * über tk_self_update_bootstrap(__FILE__) eine eigene Updater-Instanz.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

if ( ! function_exists( 'tk_self_update_bootstrap' ) ) {
	function tk_self_update_bootstrap( $plugin_file ) {
		if ( ! class_exists( 'TK_Self_Update', false ) ) {
			return null;
		}

		static $instances = [];

		$plugin_file = wp_normalize_path( $plugin_file );
		$plugin_key  = plugin_basename( $plugin_file );

		if ( isset( $instances[ $plugin_key ] ) ) {
			return $instances[ $plugin_key ];
		}

		$instance = new TK_Self_Update( $plugin_file );
		$instance->register_hooks();

		$instances[ $plugin_key ] = $instance;

		return $instance;
	}
}

if ( ! class_exists( 'TK_Self_Update', false ) ) {

	class TK_Self_Update {

		private string $plugin_file;
		private string $plugin_basename;
		private ?array $plugin_headers = null;

		public function __construct( string $plugin_file ) {
			$this->plugin_file     = wp_normalize_path( $plugin_file );
			$this->plugin_basename = plugin_basename( $this->plugin_file );
		}

		public function register_hooks(): void {
			$headers    = $this->get_plugin_headers();
			$update_uri = trim( (string) ( $headers['UpdateURI'] ?? '' ) );

			if ( $update_uri === '' ) {
				return;
			}

			$host = wp_parse_url( $update_uri, PHP_URL_HOST );

			if ( empty( $host ) ) {
				return;
			}

			add_filter( 'update_plugins_' . $host, [ $this, 'filter_update_response' ], 10, 4 );
			add_filter( 'plugins_api', [ $this, 'filter_plugin_information' ], 20, 3 );
			add_filter( 'pre_set_site_transient_update_plugins', [ $this, 'inject_update_transient' ] );
			add_filter( 'site_transient_update_plugins', [ $this, 'inject_update_transient' ] );
			add_filter( 'plugin_row_meta', [ $this, 'filter_plugin_row_meta' ], 10, 2 );
		}

		private function get_plugin_headers(): array {
			if ( null !== $this->plugin_headers ) {
				return $this->plugin_headers;
			}

			$this->plugin_headers = get_file_data(
				$this->plugin_file,
				[
					'Name'        => 'Plugin Name',
					'Version'     => 'Version',
					'Description' => 'Description',
					'PluginURI'   => 'Plugin URI',
					'Author'      => 'Author',
					'AuthorURI'   => 'Author URI',
					'RequiresWP'  => 'Requires at least',
					'RequiresPHP' => 'Requires PHP',
					'UpdateURI'   => 'Update URI',
				],
				'plugin'
			);

			return $this->plugin_headers;
		}

		private function get_metadata_url(): string {
			$headers    = $this->get_plugin_headers();
			$update_uri = trim( (string) ( $headers['UpdateURI'] ?? '' ) );

			if ( $update_uri === '' ) {
				return '';
			}

			return $update_uri;
		}

		private function get_slug(): string {
			$slug = dirname( $this->plugin_basename );

			if ( $slug === '.' || $slug === '' ) {
				$slug = basename( $this->plugin_basename, '.php' );
			}

			return $slug;
		}

		private function get_remote_metadata() {
			$url = $this->get_metadata_url();

			if ( $url === '' ) {
				return false;
			}

			$response = wp_remote_get(
				$url,
				[
					'timeout' => 15,
					'headers' => [
						'Accept' => 'application/json',
					],
				]
			);

			if ( is_wp_error( $response ) ) {
				return false;
			}

			$code = (int) wp_remote_retrieve_response_code( $response );

			if ( 200 !== $code ) {
				return false;
			}

			$body = wp_remote_retrieve_body( $response );

			if ( ! is_string( $body ) || $body === '' ) {
				return false;
			}

			$data = json_decode( $body, true );

			if ( ! is_array( $data ) || empty( $data['version'] ) ) {
				return false;
			}

			return $data;
		}

		public function filter_update_response( $update, $plugin_data, $plugin_file, $locales ) {
			if ( $plugin_file !== $this->plugin_basename ) {
				return $update;
			}

			$remote  = $this->get_remote_metadata();
			$headers = $this->get_plugin_headers();

			if ( ! $remote ) {
				return false;
			}

			$current_version = ! empty( $headers['Version'] ) ? (string) $headers['Version'] : '0.0.0';
			$new_version     = (string) $remote['version'];

			if ( version_compare( $new_version, $current_version, '<=' ) ) {
				return false;
			}

			return [
				'id'           => (string) ( $headers['UpdateURI'] ?? '' ),
				'slug'         => $this->get_slug(),
				'plugin'       => $this->plugin_basename,
				'version'      => $new_version,
				'url'          => ! empty( $remote['homepage'] ) ? (string) $remote['homepage'] : '',
				'package'      => ! empty( $remote['download_url'] ) ? (string) $remote['download_url'] : '',
				'tested'       => ! empty( $remote['tested'] ) ? (string) $remote['tested'] : '',
				'requires_php' => ! empty( $remote['requires_php'] ) ? (string) $remote['requires_php'] : '',
				'requires'     => ! empty( $remote['requires'] ) ? (string) $remote['requires'] : '',
			];
		}

		public function inject_update_transient( $transient ) {
			if ( ! is_object( $transient ) ) {
				$transient = new stdClass();
			}

			if ( ! isset( $transient->response ) || ! is_array( $transient->response ) ) {
				$transient->response = [];
			}

			if ( ! isset( $transient->no_update ) || ! is_array( $transient->no_update ) ) {
				$transient->no_update = [];
			}

			$remote  = $this->get_remote_metadata();
			$headers = $this->get_plugin_headers();

			if ( ! $remote ) {
				return $transient;
			}

			$current_version = ! empty( $headers['Version'] ) ? (string) $headers['Version'] : '0.0.0';
			$new_version     = ! empty( $remote['version'] ) ? (string) $remote['version'] : $current_version;

			$item = (object) [
				'id'           => ! empty( $headers['UpdateURI'] ) ? (string) $headers['UpdateURI'] : '',
				'slug'         => $this->get_slug(),
				'plugin'       => $this->plugin_basename,
				'new_version'  => $new_version,
				'url'          => ! empty( $remote['homepage'] ) ? (string) $remote['homepage'] : '',
				'package'      => ! empty( $remote['download_url'] ) ? (string) $remote['download_url'] : '',
				'tested'       => ! empty( $remote['tested'] ) ? (string) $remote['tested'] : '',
				'requires'     => ! empty( $remote['requires'] ) ? (string) $remote['requires'] : '',
				'requires_php' => ! empty( $remote['requires_php'] ) ? (string) $remote['requires_php'] : '',
			];

			if ( version_compare( $new_version, $current_version, '>' ) ) {
				$transient->response[ $this->plugin_basename ] = $item;
				unset( $transient->no_update[ $this->plugin_basename ] );
			} else {
				$transient->no_update[ $this->plugin_basename ] = $item;
				unset( $transient->response[ $this->plugin_basename ] );
			}

			return $transient;
		}

		public function filter_plugin_information( $result, $action, $args ) {
			if ( 'plugin_information' !== $action ) {
				return $result;
			}

			if ( empty( $args->slug ) || $args->slug !== $this->get_slug() ) {
				return $result;
			}

			$remote  = $this->get_remote_metadata();
			$headers = $this->get_plugin_headers();

			if ( ! $remote ) {
				return $result;
			}

			$info = new stdClass();

			$info->name          = ! empty( $remote['name'] ) ? (string) $remote['name'] : (string) ( $headers['Name'] ?? '' );
			$info->slug          = $this->get_slug();
			$info->version       = ! empty( $remote['version'] ) ? (string) $remote['version'] : (string) ( $headers['Version'] ?? '' );
			$info->author        = ! empty( $remote['author'] ) ? (string) $remote['author'] : (string) ( $headers['Author'] ?? '' );
			$info->homepage      = ! empty( $remote['homepage'] ) ? (string) $remote['homepage'] : (string) ( $headers['PluginURI'] ?? '' );
			$info->requires      = ! empty( $remote['requires'] ) ? (string) $remote['requires'] : (string) ( $headers['RequiresWP'] ?? '' );
			$info->requires_php  = ! empty( $remote['requires_php'] ) ? (string) $remote['requires_php'] : (string) ( $headers['RequiresPHP'] ?? '' );
			$info->tested        = ! empty( $remote['tested'] ) ? (string) $remote['tested'] : '';
			$info->download_link = ! empty( $remote['download_url'] ) ? (string) $remote['download_url'] : '';

			$description = '';

			if ( ! empty( $remote['sections']['description'] ) ) {
				$description = (string) $remote['sections']['description'];
			} elseif ( ! empty( $headers['Description'] ) ) {
				$description = (string) $headers['Description'];
			}

			$changelog = '';

			if ( ! empty( $remote['sections']['changelog'] ) ) {
				$changelog = (string) $remote['sections']['changelog'];
			}

			$info->sections = [
				'description' => $description,
				'changelog'   => $changelog,
			];

			return $info;
		}

		public function filter_plugin_row_meta( $links, $plugin_file ) {
			if ( $plugin_file !== $this->plugin_basename ) {
				return $links;
			}

			$headers    = $this->get_plugin_headers();
			$plugin_uri = trim( (string) ( $headers['PluginURI'] ?? '' ) );

			if ( $plugin_uri === '' ) {
				return $links;
			}

			$host = wp_parse_url( $plugin_uri, PHP_URL_HOST );

			if ( strtolower( (string) $host ) !== 'github.com' ) {
				return $links;
			}

			$links[] = '<a href="' . esc_url( $plugin_uri ) . '" target="_blank" rel="noopener noreferrer">GitHub Repository</a>';

			return $links;
		}
	}
}
