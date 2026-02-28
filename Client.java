import java.io.OutputStream;
import java.net.Socket;

public class Client {
    public static void main (String[] args) throws Exception {
        String host = args[0];
        int port = Integer.parseInt(args[1]);
        String message = (args.length < 3) ? "ciao!": args[2];
        Socket s = new Socket(host, port);
        OutputStream os = s.getOutputStream();
        os.write((message + "\n").getBytes());
        os.flush();
        os.close();
        s.close();
    }
}