use tauri::{WebviewUrl, WebviewWindowBuilder};

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let url = "http://127.0.0.1:18789".parse().unwrap();
            let data = std::env::var("PHILO_PROBE_OUT")
                .expect("PHILO_PROBE_OUT must point to a temporary probe directory");
            let data = std::path::PathBuf::from(data);
            assert!(data.is_absolute());
            std::fs::create_dir_all(&data)?;
            let _window = WebviewWindowBuilder::new(app, "probe", WebviewUrl::External(url))
                .title("HoldSpeak Philo static host probe")
                .inner_size(1440.0, 900.0)
                .visible(false)
                .data_directory(data)
                .initialization_script("window.desktopHost=Object.freeze({kind:'tauri',capabilities:Object.freeze({files:false,shortcuts:false,tray:false,notifications:false})});")
                .on_navigation(|url| url.scheme() == "http" && url.host_str() == Some("127.0.0.1") && url.port() == Some(18789))
                .on_page_load(|_webview, payload| {
                    println!("PHILO_PAGE_EVENT {:?} {}", payload.event(), payload.url());
                })
                .build()?;
            let handle = app.handle().clone();
            std::thread::spawn(move || {
                std::thread::sleep(std::time::Duration::from_secs(6));
                println!("PHILO_EXIT static bundle probe; no native capability commands registered");
                handle.exit(0);
            });
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("Tauri host probe failed");
}
