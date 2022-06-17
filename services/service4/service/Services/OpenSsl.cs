using System.Diagnostics;
using System.Numerics;
using System.Text;
using System.Threading.Tasks;

namespace service.Services;

public class OpenSsl
{
    private readonly string _path;

    public OpenSsl(string path)
    {
        _path = path;
    }

    public async Task<BigInteger> Prime(int bits)
    {
        var outputBuilder = new StringBuilder();

        var processStartInfo = new ProcessStartInfo
        {
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardInput = true,
            UseShellExecute = false,
            FileName = _path,
            Arguments = $"prime -generate -bits {bits}",
        };

        var process = new Process();
        process.StartInfo = processStartInfo;
        process.EnableRaisingEvents = true;
        process.OutputDataReceived += delegate (object _, DataReceivedEventArgs e) { outputBuilder.Append(e.Data); };

        process.Start();
        process.BeginOutputReadLine();
        await process.WaitForExitAsync();
        process.CancelOutputRead();

        var output = outputBuilder.ToString();
        return BigInteger.Parse(output.Trim());
    }
}
